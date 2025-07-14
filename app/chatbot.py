import streamlit as st
from services.qa_pipeline import query_knowledgebase
from services.file_manager import file_manager
from services.conversation_manager import conversation_manager
from services.file_processor import file_processor
from config import PROCESSING_DELAY_SECONDS
import time

st.title("Bot Assistant")
st.caption("Upload documents or ask questions")

# Initialize session state for conversation
if "history" not in st.session_state:
    st.session_state.history = []
if "pending_bot_reply" not in st.session_state:
    st.session_state.pending_bot_reply = False
if "processing_started" not in st.session_state:
    st.session_state.processing_started = False
if "file_uploader_key" not in st.session_state:
    st.session_state.file_uploader_key = 0

with st.sidebar:
    st.header("📂 Upload Files")
    uploaded_files = st.file_uploader(
        "Upload PDF/TXT files",
        type=["pdf", "txt"],
        accept_multiple_files=True,
        key=f"file_uploader_{st.session_state.file_uploader_key}"
    )
    
    # Handle file uploads
    if uploaded_files:
        # Update processor with current files list
        file_processor.update_files_list(uploaded_files)
        
        # Start processing if not already processing and not in bot reply
        if not file_processor.is_processing() and not st.session_state.pending_bot_reply:
            # Only try to start processing if we're not already in a processing cycle
            if file_processor.state.status.value == "idle" and not st.session_state.processing_started:
                success, message = file_processor.start_processing(uploaded_files)
                if success:
                    st.session_state.processing_started = True
                    st.rerun()
                else:
                    # If all files are already in the database, show toast, then reset uploader after delay
                    st.toast(message, icon="ℹ️")
                    time.sleep(2)
                    st.session_state.file_uploader_key += 1
                    st.rerun()
        
        # Continue processing if in progress
        if file_processor.is_processing():
            progress, message = file_processor.get_progress()
            if progress is not None:
                st.progress(progress)
                if message:
                    st.text(message)
            
            # Process next file
            if file_processor.process_next_file(uploaded_files):
                # Small delay to show progress
                time.sleep(PROCESSING_DELAY_SECONDS)
                st.rerun()
            else:
                # Processing complete or cancelled
                if file_processor.state.status.value == "completed":
                    # Reset processor after completion
                    file_processor.reset()
                    st.session_state.processing_started = False
                    # Wait for toast to disappear before clearing uploader
                    time.sleep(2)
                    st.session_state.file_uploader_key += 1
                st.rerun()
    
    else:
        # No files uploaded - cancel any ongoing processing only if it was started
        if file_processor.is_processing() and st.session_state.processing_started:
            file_processor.cancel_processing("Processing cancelled - no files selected")
            file_processor.reset()
            # Wait for toast to disappear before clearing uploader
            time.sleep(2)
            st.session_state.file_uploader_key += 1
        # Reset processing started flag when no files
        st.session_state.processing_started = False
    
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
        st.session_state.pending_bot_reply = False
        # Don't reset file processor here - let it continue if processing
        st.rerun()
    
    st.divider()
    st.header("🗄️ Database Management")
    
    # Get database statistics
    db_stats = file_manager.get_database_statistics()
    
    # Display database stats
    if db_stats['total_documents'] > 0:
        st.info(f"📊 Database: {db_stats['total_documents']} chunks from {db_stats['unique_files']} files")
        
        # Show file breakdown in an expander
        with st.expander("📄 File Details"):
            for filename, info in db_stats['files_breakdown'].items():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(f"📄 {filename}")
                    st.caption(f"{info['chunk_count']} chunks")
                with col2:
                    if st.button("🗑️", key=f"remove_{filename}", help=f"Remove {filename}"):
                        # Stop any ongoing file processing first
                        if file_processor.is_processing():
                            file_processor.cancel_processing("Processing cancelled - removing file")
                            file_processor.reset()
                        
                        with st.spinner(f"Removing {filename}..."):
                            try:
                                print(f"UI: Attempting to remove file: {filename}")
                                
                                # Check if file exists before removal
                                if not file_manager.file_exists_in_database(filename):
                                    st.warning(f"⚠️ File {filename} not found in database")
                                else:
                                    # Attempt removal
                                    if file_manager.remove_documents_by_filename(filename):
                                        st.toast(f"Successfully removed {filename}", icon="✅")
                                        # Wait for toast to disappear before clearing uploader
                                        time.sleep(2)
                                        st.session_state.file_uploader_key += 1
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Failed to remove {filename}")
                                        st.error("Check the terminal/console for detailed error information")
                                    
                            except Exception as e:
                                st.error(f"❌ Error removing {filename}: {str(e)}")
                                print(f"UI Error removing {filename}: {str(e)}")
                                import traceback
                                traceback.print_exc()
                                # Even on error, try to refresh the UI
                                st.rerun()
        
        # Clear all documents button
        if st.button("🗑️ Clear All Documents", use_container_width=True):
            # Stop any ongoing file processing first
            if file_processor.is_processing():
                file_processor.cancel_processing("Processing cancelled - clearing database")
                file_processor.reset()
            
            with st.spinner("Clearing all documents..."):
                try:
                    # Clear the database
                    if file_manager.clear_all_documents():
                        st.toast("All documents cleared", icon="✅")
                        # Wait for toast to disappear before clearing uploader
                        time.sleep(2)
                        st.session_state.file_uploader_key += 1
                        # Force a rerun to refresh the UI
                        st.rerun()
                    else:
                        st.error("❌ Failed to clear documents")
                except Exception as e:
                    st.error(f"❌ Error clearing documents: {str(e)}")
                    # Even on error, try to refresh the UI
                    st.rerun()
    else:
        st.info("📊 Database is empty")

user_input = st.chat_input("Type your question here...")
if user_input:
    submit_input = user_input.strip()
    if submit_input:
        # Truncate history if needed before adding new message
        if conversation_manager.should_truncate_history(st.session_state.history):
            st.session_state.history = conversation_manager.truncate_history(st.session_state.history)
        
        st.session_state.history.append({"role": "user", "content": submit_input})
        st.session_state.pending_bot_reply = True
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

if st.session_state.pending_bot_reply:
    with st.spinner("Bot is typing..."):
        # Get the current question
        current_question = st.session_state.history[-1]["content"]
        # Get conversation history (exclude the current question)
        conversation_history = st.session_state.history[:-1]
        
        # Query with conversation context
        answer = query_knowledgebase(current_question, conversation_history)
        
    st.session_state.history.append({"role": "assistant", "content": answer})
    st.session_state.pending_bot_reply = False
    st.rerun()