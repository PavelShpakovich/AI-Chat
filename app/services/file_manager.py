from langchain_chroma import Chroma
from services.embeddings import ollama_embeddings
from typing import Dict, List, Optional
import os
from collections import defaultdict

class FileManager:
    """
    Service for managing files in the vector database.
    Handles file existence checking, removal, and database statistics.
    """
    
    def __init__(self):
        self.vectorstore = Chroma(
            embedding_function=ollama_embeddings,
            persist_directory="./db/chroma_db",
            collection_name="confluence_knowledge_base"
        )
    
    def file_exists_in_database(self, filename: str) -> bool:
        """
        Check if a file already exists in the database based on filename metadata.
        
        Args:
            filename: Name of the file to check
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            # More efficient check using a where filter
            results = self.vectorstore.get(where={"filename": filename}, limit=1)
            return bool(results and results.get('ids'))
        except Exception as e:
            print(f"Error checking file existence: {e}")
            return False
    
    def remove_documents_by_filename(self, filename: str) -> bool:
        """
        Remove all documents from the database that match the given filename.
        
        Args:
            filename: Name of the file to remove
            
        Returns:
            True if removal was successful, False otherwise
        """
        try:
            print(f"Attempting to remove documents for file: {filename}")
            
            # Check if the file exists first
            if not self.file_exists_in_database(filename):
                print(f"No documents found for file: {filename}")
                return True # Or False, depending on desired behavior for non-existent files

            # More efficient deletion using a where filter
            ids_to_remove = self.vectorstore.get(where={"filename": filename})['ids']
            if not ids_to_remove:
                print(f"No document IDs found for file: {filename}")
                return True

            self.vectorstore._collection.delete(ids=ids_to_remove)
            
            # Verify removal
            if not self.file_exists_in_database(filename):
                print(f"✅ Successfully removed documents for file: {filename}")
                return True
            else:
                print(f"❌ Removal verification failed for file: {filename}")
                return False
                
        except Exception as e:
            print(f"Error removing documents for file {filename}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def clear_all_documents(self) -> bool:
        """
        Clear all documents from the database.
        
        Returns:
            True if clearing was successful, False otherwise
        """
        try:
            # Get all document IDs
            collection = self.vectorstore.get()
            if collection and 'ids' in collection and collection['ids']:
                # Use the collection's delete method directly
                self.vectorstore._collection.delete(ids=collection['ids'])
                print("All documents cleared from database")
                
                # Verify the database is actually empty
                verification_collection = self.vectorstore.get(limit=1)
                if verification_collection and verification_collection.get('ids'):
                    print("Warning: Database may not be completely cleared")
                    return False
                
                return True
            else:
                print("Database is already empty")
                return True
        except Exception as e:
            print(f"Error clearing database: {e}")
            return False
    
    def get_database_statistics(self) -> Dict:
        """
        Get detailed statistics about the database contents.
        
        Returns:
            Dictionary containing database statistics
        """
        try:
            collection = self.vectorstore.get()
            if not collection or 'metadatas' not in collection:
                return {
                    'total_documents': 0,
                    'unique_files': 0,
                    'files_breakdown': {}
                }
            
            # Count documents per file
            file_counts = defaultdict(int)
            for metadata in collection['metadatas']:
                if metadata:
                    filename = metadata.get('filename', 'unknown')
                    file_counts[filename] += 1
            
            # Create files breakdown
            files_breakdown = {}
            for filename, count in file_counts.items():
                files_breakdown[filename] = {
                    'chunk_count': count
                }
            
            return {
                'total_documents': len(collection['ids']),
                'unique_files': len(file_counts),
                'files_breakdown': files_breakdown
            }
            
        except Exception as e:
            print(f"Error getting database statistics: {e}")
            return {
                'total_documents': 0,
                'unique_files': 0,
                'files_breakdown': {}
            }
    
    def debug_database_contents(self) -> Dict:
        """
        Debug function to inspect database contents.
        
        Returns:
            Dictionary with debug information
        """
        try:
            collection = self.vectorstore.get()
            
            debug_info = {
                'has_collection': collection is not None,
                'has_ids': 'ids' in collection if collection else False,
                'has_metadatas': 'metadatas' in collection if collection else False,
                'total_documents': len(collection['ids']) if collection and 'ids' in collection else 0,
                'sample_metadata': []
            }
            
            if collection and 'metadatas' in collection:
                # Show first 5 metadata entries
                for i, metadata in enumerate(collection['metadatas'][:5]):
                    debug_info['sample_metadata'].append({
                        'index': i,
                        'metadata': metadata,
                        'id': collection['ids'][i] if 'ids' in collection and i < len(collection['ids']) else None
                    })
            
            return debug_info
            
        except Exception as e:
            return {
                'error': str(e),
                'has_collection': False,
                'has_ids': False,
                'has_metadatas': False,
                'total_documents': 0,
                'sample_metadata': []
            }

    def list_all_files(self) -> List[str]:
        """
        Get a list of all unique filenames in the database.
        
        Returns:
            List of filenames
        """
        try:
            collection = self.vectorstore.get()
            if not collection or 'metadatas' not in collection:
                return []
            
            filenames = set()
            for metadata in collection['metadatas']:
                if metadata and metadata.get('filename'):
                    filenames.add(metadata.get('filename'))
            
            return sorted(list(filenames))
            
        except Exception as e:
            print(f"Error listing files: {e}")
            return []
    
    def get_file_info(self, filename: str) -> Optional[Dict]:
        """
        Get detailed information about a specific file.
        
        Args:
            filename: Name of the file to get info for
            
        Returns:
            Dictionary with file information or None if not found
        """
        try:
            collection = self.vectorstore.get()
            if not collection or 'metadatas' not in collection:
                return None
            
            chunk_count = 0
            sources = set()
            
            for metadata in collection['metadatas']:
                if metadata and metadata.get('filename') == filename:
                    chunk_count += 1
                    if metadata.get('source'):
                        sources.add(metadata.get('source'))
            
            if chunk_count == 0:
                return None
            
            return {
                'filename': filename,
                'chunk_count': chunk_count,
                'sources': list(sources)
            }
            
        except Exception as e:
            print(f"Error getting file info for {filename}: {e}")
            return None

# Create a singleton instance
file_manager = FileManager()
