from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from services.embeddings import ollama_embeddings
from services.llm import OllamaLLM
from services.conversation_manager import conversation_manager
from typing import List, Dict, Tuple

vectorstore = Chroma(
    embedding_function=ollama_embeddings,
    persist_directory="./db/chroma_db",
    collection_name="confluence_knowledge_base"
)

llm = OllamaLLM(model_name="llama3.1:latest")

def get_dynamic_text_splitter(text_length: int) -> RecursiveCharacterTextSplitter:
    """
    Create a text splitter with dynamic parameters based on text length.
    
    Args:
        text_length: Total length of the text to be split
        
    Returns:
        RecursiveCharacterTextSplitter with optimized parameters
    """
    if text_length <= 5000:
        # Small documents: smaller chunks for better granularity
        chunk_size = 500
        chunk_overlap = 100
    elif text_length <= 20000:
        # Medium documents: standard chunks
        chunk_size = 1000
        chunk_overlap = 200
    elif text_length <= 50000:
        # Large documents: larger chunks for better context
        chunk_size = 1500
        chunk_overlap = 300
    else:
        # Very large documents: even larger chunks
        chunk_size = 2000
        chunk_overlap = 400
    
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )

def analyze_document_content(docs) -> Dict[str, any]:
    """
    Analyze document content to determine optimal splitting strategy.
    
    Args:
        docs: List of document objects
        
    Returns:
        Dictionary with content analysis results
    """
    total_length = sum(len(doc.page_content) for doc in docs)
    avg_page_length = total_length / len(docs) if docs else 0
    
    # Analyze content structure
    newline_density = sum(doc.page_content.count('\n') for doc in docs) / total_length if total_length > 0 else 0
    paragraph_density = sum(doc.page_content.count('\n\n') for doc in docs) / total_length if total_length > 0 else 0
    
    content_type = "structured" if paragraph_density > 0.01 else "continuous"
    
    return {
        "total_length": total_length,
        "avg_page_length": avg_page_length,
        "newline_density": newline_density,
        "paragraph_density": paragraph_density,
        "content_type": content_type,
        "num_pages": len(docs)
    }

def get_optimized_text_splitter(docs) -> Tuple[RecursiveCharacterTextSplitter, int]:
    """
    Get an optimized text splitter based on document analysis.
    
    Args:
        docs: List of document objects
        
    Returns:
        Tuple of (RecursiveCharacterTextSplitter, chunk_size) with optimized parameters
    """
    analysis = analyze_document_content(docs)
    
    # Base parameters from dynamic splitting
    base_splitter = get_dynamic_text_splitter(analysis["total_length"])
    
    # Get chunk size and overlap from the base splitter
    try:
        base_chunk_size = base_splitter._chunk_size
        base_overlap = base_splitter._chunk_overlap
    except AttributeError:
        # Fallback to default values if attributes aren't available
        if analysis["total_length"] <= 5000:
            base_chunk_size, base_overlap = 500, 100
        elif analysis["total_length"] <= 20000:
            base_chunk_size, base_overlap = 1000, 200
        elif analysis["total_length"] <= 50000:
            base_chunk_size, base_overlap = 1500, 300
        else:
            base_chunk_size, base_overlap = 2000, 400
    
    # Adjust based on content structure
    if analysis["content_type"] == "structured":
        # For structured content, prioritize paragraph breaks
        separators = ["\n\n", "\n", ". ", " ", ""]
        # Slightly smaller chunks for structured content
        chunk_size = int(base_chunk_size * 0.9)
    else:
        # For continuous content, use standard separators
        separators = ["\n\n", "\n", " ", ""]
        chunk_size = base_chunk_size
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=base_overlap,
        length_function=len,
        separators=separators
    )
    
    return splitter, chunk_size

# Default text splitter for backward compatibility
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)

# Enhanced prompt template for better conversational flow
CONVERSATIONAL_QA_PROMPT = PromptTemplate(
    input_variables=["context", "question", "chat_history"],
    template="""You are a helpful AI assistant. Answer the question using the provided context and maintain natural conversation flow.

{chat_history}Context:
{context}

Question: {question}

Provide a clear, helpful answer. If you don't have enough information, say so. Keep your response natural and conversational.

Answer:"""
)

def format_chat_history(history: List[Dict[str, str]]) -> str:
    """Format chat history for inclusion in prompt using conversation manager."""
    formatted_history = conversation_manager.format_history_for_llm(history)
    
    # If there's no history, return empty string to avoid "No previous conversation" text
    if formatted_history == "No previous conversation.":
        return ""
    
    # Add a natural prefix for conversation context
    return f"Previous conversation:\n{formatted_history}\n"

def get_chunk_statistics(chunks) -> Dict[str, any]:
    """
    Get statistics about the generated chunks.
    
    Args:
        chunks: List of text chunks
        
    Returns:
        Dictionary with chunk statistics
    """
    if not chunks:
        return {"count": 0, "avg_length": 0, "min_length": 0, "max_length": 0}
    
    lengths = [len(chunk.page_content) for chunk in chunks]
    
    return {
        "count": len(chunks),
        "avg_length": sum(lengths) / len(lengths),
        "min_length": min(lengths),
        "max_length": max(lengths),
        "total_length": sum(lengths)
    }

def process_uploaded_files(files):
    documents = []
    file_stats = []
    
    for file_info in files:
        file_path = file_info['path']
        file_ext = file_info['ext']
        
        try:
            if file_ext == '.pdf':
                loader = PyPDFLoader(file_path)
            elif file_ext == '.txt':
                loader = TextLoader(file_path, encoding='utf-8')
            else:
                continue
                
            docs = loader.load()
            
            # Use optimized text splitter based on document analysis
            optimized_splitter, chunk_size = get_optimized_text_splitter(docs)
            split_docs = optimized_splitter.split_documents(docs)
            
            documents.extend(split_docs)
            
            # Get detailed statistics
            analysis = analyze_document_content(docs)
            chunk_stats = get_chunk_statistics(split_docs)
            
            file_stats.append({
                "name": file_info['name'],
                "pages": len(docs),
                "chunks": len(split_docs),
                "analysis": analysis,
                "chunk_stats": chunk_stats,
                "chunk_size": chunk_size
            })
            
            print(f"📄 {file_info['name']}: {len(docs)} pages → {len(split_docs)} chunks")
            print(f"   Text: {analysis['total_length']:,} chars, Type: {analysis['content_type']}")
            print(f"   Chunks: avg {chunk_stats['avg_length']:.0f} chars, "
                  f"range {chunk_stats['min_length']}-{chunk_stats['max_length']}")
            
        except Exception as e:
            print(f"❌ Error processing file {file_info['name']}: {e}")
            continue
    
    if documents:
        try:
            vectorstore.add_documents(documents)
            
            # Print summary statistics
            total_chunks = len(documents)
            total_files = len(file_stats)
            avg_chunks_per_file = total_chunks / total_files if total_files > 0 else 0
            
            print(f"\n📊 Processing Summary:")
            print(f"   Files processed: {total_files}")
            print(f"   Total chunks: {total_chunks}")
            print(f"   Average chunks per file: {avg_chunks_per_file:.1f}")
            print(f"✅ Successfully added to vector store")
            
            return True
        except Exception as e:
            print(f"❌ Error adding to vector store: {e}")
            return False
    
    return False

retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 4})

# Create a custom chain with conversation history support
def create_conversational_qa_chain():
    """Create a QA chain that supports conversation history."""
    
    def _get_inputs(inputs):
        """Extract inputs for the chain."""
        question = inputs.get("question", "")
        chat_history = inputs.get("chat_history", [])
        
        # Get relevant documents
        docs = retriever.get_relevant_documents(question)
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # Format chat history
        formatted_history = format_chat_history(chat_history)
        
        # Create the prompt
        prompt = CONVERSATIONAL_QA_PROMPT.format(
            context=context,
            question=question,
            chat_history=formatted_history
        )
        
        return prompt
    
    def _call_llm(prompt):
        """Call the LLM with the formatted prompt."""
        try:
            response = llm.invoke(prompt)
            return response
        except Exception as e:
            print(f"LLM error: {e}")
            return "I apologize, but I encountered an error processing your question."
    
    def chain_func(inputs):
        """Main chain function."""
        prompt = _get_inputs(inputs)
        result = _call_llm(prompt)
        return {"result": result}
    
    return chain_func

# Initialize the conversational chain
conversational_qa_chain = create_conversational_qa_chain()

def query_knowledgebase(question: str, chat_history: List[Dict[str, str]] = None) -> str:
    """
    Query the knowledge base with conversation history support.
    
    Args:
        question: The user's current question
        chat_history: List of previous messages in format [{"role": "user/assistant", "content": "..."}]
    
    Returns:
        The assistant's response
    """
    if chat_history is None:
        chat_history = []
    
    try:
        result = conversational_qa_chain({
            "question": question,
            "chat_history": chat_history
        })
        return result.get("result", "No answer found.")
    except Exception as e:
        print(f"Query error: {e}")
        return "Sorry, I encountered an error processing your question."