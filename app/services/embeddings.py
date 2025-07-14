"""
Ollama embedding services for the app.
"""
from langchain_ollama import OllamaEmbeddings 

# Example usage:
ollama_embeddings = OllamaEmbeddings(
    base_url="http://localhost:11434",
    model="nomic-embed-text:v1.5"
)

