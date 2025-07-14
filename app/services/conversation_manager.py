"""
Conversation management utilities for maintaining chat context.
"""
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ConversationConfig:
    """Configuration for conversation management."""
    max_history_length: int = 10  # Maximum number of messages to keep
    max_context_length: int = 6   # Maximum messages to include in LLM context

class ConversationManager:
    """Manages conversation history and context."""
    
    def __init__(self, config: ConversationConfig = None):
        self.config = config or ConversationConfig()
    
    def format_history_for_llm(self, history: List[Dict[str, str]]) -> str:
        """
        Format conversation history for LLM context.
        
        Args:
            history: List of messages in format [{"role": "user/assistant", "content": "..."}]
            
        Returns:
            Formatted string for LLM prompt
        """
        if not history:
            return "No previous conversation."
        
        # Take only the most recent messages within context limit
        recent_history = history[-self.config.max_context_length:]
        
        formatted_messages = []
        for message in recent_history:
            role = message.get("role", "")
            content = message.get("content", "")
            
            if role == "user":
                formatted_messages.append(f"User: {content}")
            elif role == "assistant":
                formatted_messages.append(f"Assistant: {content}")
        
        return "\n".join(formatted_messages) if formatted_messages else "No previous conversation."
    
    def should_truncate_history(self, history: List[Dict[str, str]]) -> bool:
        """Check if conversation history should be truncated."""
        return len(history) > self.config.max_history_length
    
    def truncate_history(self, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Truncate conversation history to maintain performance.
        Keeps the most recent messages within the limit.
        """
        if len(history) <= self.config.max_history_length:
            return history
        
        # Keep the most recent messages
        return history[-self.config.max_history_length:]
    
    def get_conversation_summary(self, history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Get summary statistics about the conversation."""
        if not history:
            return {"total_messages": 0, "user_messages": 0, "assistant_messages": 0}
        
        user_messages = sum(1 for msg in history if msg.get("role") == "user")
        assistant_messages = sum(1 for msg in history if msg.get("role") == "assistant")
        
        return {
            "total_messages": len(history),
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "last_message_time": datetime.now().isoformat()
        }

# Global conversation manager instance
conversation_manager = ConversationManager()
