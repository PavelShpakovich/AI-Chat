"""
Central configuration and environment variable access for the app.
"""
import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

MILVUS_HOST = os.getenv("MILVUS_HOST")
MILVUS_PORT = os.getenv("MILVUS_PORT")
MILVUS_URI = os.getenv("MILVUS_URI")
MILVUS_TOKEN = os.getenv("MILVUS_TOKEN")

# File upload settings
SUPPORTED_FILE_TYPES = ["pdf", "txt"]
MAX_FILE_SIZE_MB = 100  # Maximum file size in MB
MAX_FILES_PER_UPLOAD = 10  # Maximum number of files per upload

# Processing settings
PROCESSING_DELAY_SECONDS = 0.1  # Delay between file processing steps
MAX_RETRIES = 3  # Maximum retries for failed operations

# Database settings
DB_PERSIST_DIRECTORY = "./db/chroma_db"
DB_COLLECTION_NAME = "confluence_knowledge_base"

# LLM settings
DEFAULT_LLM_MODEL = "llama3.1:latest"
MAX_CONTEXT_LENGTH = 8192  # Maximum context length for LLM

# Conversation settings
MAX_CONVERSATION_HISTORY = 20  # Maximum number of messages to keep in history
TRUNCATION_THRESHOLD = 15  # Truncate when history exceeds this length

# UI settings
SIDEBAR_WIDTH = 300  # Sidebar width in pixels
PROGRESS_BAR_HEIGHT = 20  # Progress bar height in pixels

# Error messages
ERROR_MESSAGES = {
    "file_not_found": "File not found or has been removed",
    "processing_failed": "Failed to process file",
    "database_error": "Database operation failed",
    "llm_error": "Language model error occurred",
    "invalid_file_type": "Invalid file type. Supported types: {types}",
    "file_too_large": "File too large. Maximum size: {size}MB",
    "too_many_files": "Too many files. Maximum: {count} files"
}

# Success messages
SUCCESS_MESSAGES = {
    "file_processed": "File processed successfully",
    "files_processed": "All files processed successfully",
    "database_cleared": "Database cleared successfully",
    "file_removed": "File removed successfully"
}

# Status messages
STATUS_MESSAGES = {
    "starting": "Starting processing...",
    "processing": "Processing {filename}... ({current}/{total})",
    "completed": "Processing complete",
    "cancelled": "Processing cancelled",
    "skipped": "Skipped {filename} ({reason})"
}

def get_error_message(key: str, **kwargs) -> str:
    """Get formatted error message"""
    return ERROR_MESSAGES.get(key, "Unknown error").format(**kwargs)

def get_success_message(key: str, **kwargs) -> str:
    """Get formatted success message"""
    return SUCCESS_MESSAGES.get(key, "Success").format(**kwargs)

def get_status_message(key: str, **kwargs) -> str:
    """Get formatted status message"""
    return STATUS_MESSAGES.get(key, "Status").format(**kwargs)
