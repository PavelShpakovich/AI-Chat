"""
Ollama LLM service wrapper for the app.
"""
from langchain_ollama import OllamaLLM as BaseLlamaLLM

class OllamaLLM(BaseLlamaLLM):
    """Service for Ollama LLM."""
    def __init__(self, model_name: str = "llama3.1:latest", base_url: str = "http://localhost:11434", **kwargs):
        super().__init__(model=model_name, base_url=base_url, **kwargs)

    def invoke(self, input: str, config=None, **kwargs) -> str:
        return super().invoke(input, **kwargs)
