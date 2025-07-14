"""
File processing service for handling file uploads and processing.
Implements best practices for file handling and state management.
"""

import os
import tempfile
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import streamlit as st
from services.qa_pipeline import process_uploaded_files
from services.file_manager import file_manager
from config import PROCESSING_DELAY_SECONDS, get_status_message, get_error_message


class ProcessingStatus(Enum):
    """Status of file processing"""
    IDLE = "idle"
    STARTING = "starting"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class ProcessingState:
    """State of file processing"""
    status: ProcessingStatus = ProcessingStatus.IDLE
    current_file_index: int = 0
    total_files: int = 0
    current_filename: Optional[str] = None
    progress: float = 0.0
    message: str = ""
    files_to_process: List[str] = None
    
    def __post_init__(self):
        if self.files_to_process is None:
            self.files_to_process = []


class FileProcessor:
    """Handles file upload and processing logic"""
    
    def __init__(self):
        self.state_key = "file_processor_state"
        self._ensure_state()
    
    def _ensure_state(self):
        """Ensure processing state exists in session state"""
        if self.state_key not in st.session_state:
            st.session_state[self.state_key] = ProcessingState()
    
    @property
    def state(self) -> ProcessingState:
        """Get current processing state"""
        self._ensure_state()
        return st.session_state[self.state_key]
    
    def _update_state(self, **kwargs):
        """Update processing state"""
        for key, value in kwargs.items():
            setattr(self.state, key, value)
    
    def is_processing(self) -> bool:
        """Check if currently processing files"""
        return self.state.status in [ProcessingStatus.STARTING, ProcessingStatus.PROCESSING]
    
    from typing import Tuple
    def start_processing(self, uploaded_files: List) -> Tuple[bool, str]:
        """Start processing uploaded files"""
        if self.is_processing():
            return False, "Processing already in progress"
        # Filter out files that already exist in database
        new_files = [f for f in uploaded_files if not file_manager.file_exists_in_database(f.name)]
        if not new_files:
            return False, "All selected files are already in the database"
        # Initialize processing state
        self._update_state(
            status=ProcessingStatus.STARTING,
            current_file_index=0,
            total_files=len(new_files),
            files_to_process=[f.name for f in new_files],
            progress=0.0,
            message=get_status_message("starting")
        )
        return True, "Started processing"
    
    def cancel_processing(self, reason: str = "Processing cancelled") -> str:
        """Cancel current processing"""
        self._update_state(
            status=ProcessingStatus.CANCELLED,
            message=reason
        )
        return reason
    
    def process_next_file(self, uploaded_files: List) -> bool:
        """Process the next file in the queue"""
        if not self.is_processing():
            return False
        
        # Check if we have more files to process
        if self.state.current_file_index >= len(self.state.files_to_process):
            self._complete_processing()
            return False
        
        filename = self.state.files_to_process[self.state.current_file_index]
        
        # Update progress
        progress = (self.state.current_file_index + 1) / self.state.total_files
        self._update_state(
            status=ProcessingStatus.PROCESSING,
            current_filename=filename,
            progress=progress,
            message=get_status_message("processing", 
                                     filename=filename, 
                                     current=self.state.current_file_index + 1, 
                                     total=self.state.total_files)
        )
        
        # Validate file still exists and should be processed
        if not self._should_process_file(filename, uploaded_files):
            self._skip_current_file(f"Skipped {filename}")
            return True
        
        # Process the file
        success = self._process_single_file(filename, uploaded_files)
        
        # Update status based on result
        if success:
            self._update_state(message=f"✅ Processed {filename}")
        else:
            self._update_state(message=f"❌ Failed to process {filename}")
        
        # Move to next file
        self._update_state(current_file_index=self.state.current_file_index + 1)
        
        return True
    
    def _should_process_file(self, filename: str, uploaded_files: List) -> bool:
        """Check if file should be processed"""
        # Check if file already exists in database
        if file_manager.file_exists_in_database(filename):
            return False
        
        # Check if file is still in uploaded files
        uploaded_names = [f.name for f in uploaded_files] if uploaded_files else []
        if filename not in uploaded_names:
            return False
        
        # Check if file is still in processing queue
        if filename not in self.state.files_to_process:
            return False
        
        return True
    
    def _skip_current_file(self, reason: str) -> str:
        """Skip current file and move to next"""
        self._update_state(
            current_file_index=self.state.current_file_index + 1,
            message=f"⚠️ {reason}"
        )
        return reason
    
    def _process_single_file(self, filename: str, uploaded_files: List) -> bool:
        """Process a single file"""
        try:
            # Find the file object
            file_obj = None
            for f in uploaded_files:
                if f.name == filename:
                    file_obj = f
                    break
            
            if file_obj is None:
                return False
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(
                suffix=os.path.splitext(file_obj.name)[1],
                delete=False
            )
            temp_file.write(file_obj.getvalue())
            temp_file.close()
            
            temp_file_info = {
                'path': temp_file.name,
                'name': file_obj.name,
                'ext': os.path.splitext(file_obj.name)[1].lower()
            }
            
            # Create cancellation callback
            def cancellation_callback(fname):
                return self._should_process_file(fname, uploaded_files)
            
            # Process file
            success = process_uploaded_files([temp_file_info], cancellation_callback)
            
            return success
            
        except Exception as e:
            print(f"❌ Error processing file {filename}: {e}")
            return False
        finally:
            # Clean up temp file
            if 'temp_file' in locals() and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def _complete_processing(self) -> str:
        """Complete processing"""
        self._update_state(
            status=ProcessingStatus.COMPLETED,
            progress=1.0,
            message=get_status_message("completed")
        )
        return f"Successfully processed {self.state.total_files} file(s)"
    
    def reset(self):
        """Reset processing state"""
        self._update_state(
            status=ProcessingStatus.IDLE,
            current_file_index=0,
            total_files=0,
            current_filename=None,
            progress=0.0,
            message="",
            files_to_process=[]
        )
    
    def update_files_list(self, uploaded_files: List) -> Optional[str]:
        """Update the list of files being processed when files are removed"""
        if not self.is_processing():
            return None
        current_uploaded_names = [f.name for f in uploaded_files] if uploaded_files else []
        # Find files that were removed
        removed_files = [f for f in self.state.files_to_process if f not in current_uploaded_names]
        if removed_files:
            # Update the processing list
            new_files_to_process = [f for f in self.state.files_to_process if f in current_uploaded_names]
            if not new_files_to_process:
                # All files were removed
                self.cancel_processing("Processing cancelled - all files removed")
                return f"Cancelled processing for {len(removed_files)} file(s)"
            # Update state
            old_current_filename = self.state.current_filename
            self._update_state(
                files_to_process=new_files_to_process,
                total_files=len(new_files_to_process)
            )
            # Adjust current file index
            if old_current_filename and old_current_filename in new_files_to_process:
                new_index = new_files_to_process.index(old_current_filename)
                self._update_state(current_file_index=new_index)
            else:
                # Current file was removed, adjust index
                if self.state.current_file_index >= len(new_files_to_process):
                    self._update_state(current_file_index=max(0, len(new_files_to_process) - 1))
            return f"Cancelled processing for {len(removed_files)} file(s)"
        return None
    
    def get_progress(self):
        """Get progress bar value and status message"""
        if self.is_processing():
            return self.state.progress, self.state.message
        return None, None


# Create singleton instance
file_processor = FileProcessor()
