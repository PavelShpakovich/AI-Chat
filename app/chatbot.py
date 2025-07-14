import streamlit as st
from services.qa_pipeline import query_knowledgebase, process_uploaded_files
from services.conversation_manager import conversation_manager
import tempfile
import os

st.title("Bot Assistant")
st.caption("Upload documents or ask questions")

if "processed_files" not in st.session_state:
    st.session_state.processed_files = set()
if "history" not in st.session_state:
    st.session_state.history = []
if "processing_files" not in st.session_state:
    st.session_state.processing_files = False
if "last_uploaded_files" not in st.session_state:
    st.session_state.last_uploaded_files = []

with st.sidebar:
    st.header("📂 Upload Files")
    uploaded_files = st.file_uploader(
        "Upload PDF/TXT files",
        type=["pdf", "txt"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        # Check if the uploaded files have changed
        current_file_names = [f.name for f in uploaded_files]
        files_changed = current_file_names != st.session_state.last_uploaded_files
        
        new_files = [f for f in uploaded_files if f.name not in st.session_state.processed_files]
        if new_files and files_changed and not st.session_state.get("pending_bot_reply", False) and not st.session_state.processing_files:
            st.session_state.processing_files = True
            st.session_state.last_uploaded_files = current_file_names
            
            with st.spinner("Processing files..."):
                temp_files = []
                try:
                    for file in new_files:
                        temp_file = tempfile.NamedTemporaryFile(
                            suffix=os.path.splitext(file.name)[1],
                            delete=False
                        )
                        temp_file.write(file.getvalue())
                        temp_file.close()
                        temp_files.append({
                            'path': temp_file.name,
                            'name': file.name,
                            'ext': os.path.splitext(file.name)[1].lower()
                        })
                    
                    if process_uploaded_files(temp_files):
                        st.session_state.processed_files.update(f['name'] for f in temp_files)
                        st.success(f"Processed {len(new_files)} file(s)")
                finally:
                    for temp_file in temp_files:
                        if os.path.exists(temp_file['path']):
                            os.unlink(temp_file['path'])
                    st.session_state.processing_files = False
    
    st.divider()
    st.header("💬 Conversation")
    
    # Display conversation stats
    if st.session_state.history:
        stats = conversation_manager.get_conversation_summary(st.session_state.history)
        st.info(f"Messages: {stats['total_messages']} | User: {stats['user_messages']} | Assistant: {stats['assistant_messages']}")
        
        # Show if history needs truncation
        if conversation_manager.should_truncate_history(st.session_state.history):
            st.warning("⚠️ Long conversation - older messages may be truncated")
    
    # Clear conversation button
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.history = []
        st.session_state.pop("pending_bot_reply", None)
        st.session_state.processing_files = False
        st.rerun()

user_input = st.chat_input("Type your question here...")
if user_input:
    submit_input = user_input.strip()
    if submit_input:
        # Truncate history if needed before adding new message
        if conversation_manager.should_truncate_history(st.session_state.history):
            st.session_state.history = conversation_manager.truncate_history(st.session_state.history)
        
        st.session_state.history.append({"role": "user", "content": submit_input})
        st.session_state["pending_bot_reply"] = True
        st.rerun()

for chat in st.session_state.history:
    with st.chat_message(chat["role"]):
        if chat["role"] == "assistant":
            if chat["content"].strip().startswith("```") and chat["content"].strip().endswith("```"):
                st.code(chat["content"].strip().strip("`"))
            else:
                st.markdown(chat["content"])
        else:
            st.markdown(chat["content"], unsafe_allow_html=False)

if st.session_state.get("pending_bot_reply"):
    with st.spinner("Bot is typing..."):
        # Get the current question
        current_question = st.session_state.history[-1]["content"]
        # Get conversation history (exclude the current question)
        conversation_history = st.session_state.history[:-1]
        
        # Query with conversation context
        answer = query_knowledgebase(current_question, conversation_history)
        
    st.session_state.history.append({"role": "assistant", "content": answer})
    st.session_state["pending_bot_reply"] = False
    st.rerun()