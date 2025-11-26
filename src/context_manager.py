"""
Context manager for CogniOrch.
Handles conversation history, command outputs, and multi-step task coordination.
"""

import json
import os
from typing import List, Dict, Any
from datetime import datetime


class ContextManager:
    """Manages conversation context and task history for multi-step workflows."""
    
    def __init__(self, max_history_size: int = 20, max_context_tokens: int = 4000):
        """
        Initialize the context manager.
        
        Args:
            max_history_size: Maximum number of conversation entries to keep
            max_context_tokens: Approximate max tokens before summarization
        """
        self.max_history_size = max_history_size
        self.max_context_tokens = max_context_tokens
        
        # Core tracking
        self.conversation_history: List[Dict[str, Any]] = []
        self.executed_commands: List[Dict[str, Any]] = []
        self.working_directory: str = os.getcwd()
        self.session_metadata = {
            "start_time": datetime.now().isoformat(),
            "task_count": 0,
            "last_task_status": None
        }
        
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """
        Add a message to conversation history.
        
        Args:
            role: 'user', 'assistant', or 'system'
            content: Message content
            metadata: Optional metadata (commands, outputs, etc.)
        """
        entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.conversation_history.append(entry)
        
        # Manage history size
        if len(self.conversation_history) > self.max_history_size * 2:
            self._compress_history()
    
    def add_command_execution(self, command: str, output: str, success: bool = True):
        """
        Track a command execution for context.
        
        Args:
            command: The executed command
            output: Command output
            success: Whether the command succeeded
        """
        execution = {
            "command": command,
            "output": output,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "working_dir": self.working_directory
        }
        
        self.executed_commands.append(execution)
        self.session_metadata["task_count"] += 1
        self.session_metadata["last_task_status"] = "success" if success else "failed"
        
        # Keep only recent commands
        if len(self.executed_commands) > 10:
            self.executed_commands = self.executed_commands[-10:]
    
    def get_recent_context(self, num_messages: int = 10) -> str:
        """
        Get recent conversation context as a formatted string.
        
        Args:
            num_messages: Number of recent messages to include
            
        Returns:
            Formatted context string
        """
        recent = self.conversation_history[-num_messages:]
        
        context_parts = ["=== RECENT CONVERSATION CONTEXT ===\n"]
        
        for entry in recent:
            role = entry["role"].upper()
            content = entry["content"]
            context_parts.append(f"[{role}]: {content}\n")
        
        return "\n".join(context_parts)
    
    def get_command_history_summary(self) -> str:
        """
        Get a summary of recently executed commands.
        
        Returns:
            Formatted command history string
        """
        if not self.executed_commands:
            return "No commands executed yet in this session."
        
        summary_parts = ["=== RECENT COMMAND EXECUTIONS ===\n"]
        
        for cmd in self.executed_commands[-5:]:
            status = "✓" if cmd["success"] else "✗"
            summary_parts.append(f"{status} {cmd['command']}")
            # Include abbreviated output
            output_preview = cmd["output"][:200] + "..." if len(cmd["output"]) > 200 else cmd["output"]
            summary_parts.append(f"   Output: {output_preview}\n")
        
        return "\n".join(summary_parts)
    
    def build_context_for_ai(self, include_commands: bool = True) -> str:
        """
        Build comprehensive context for AI including conversation and command history.
        
        Args:
            include_commands: Whether to include command execution history
            
        Returns:
            Complete context string for AI
        """
        context_parts = []
        
        # Session metadata
        context_parts.append(f"""
=== SESSION INFO ===
Working Directory: {self.working_directory}
Tasks Completed: {self.session_metadata['task_count']}
Last Task: {self.session_metadata['last_task_status'] or 'N/A'}
""")
        
        # Command history
        if include_commands and self.executed_commands:
            context_parts.append(self.get_command_history_summary())
        
        # Recent conversation
        context_parts.append(self.get_recent_context())
        
        return "\n".join(context_parts)
    
    def _compress_history(self):
        """
        Compress old conversation history by summarizing.
        Keeps the most recent messages and summarizes older ones.
        """
        # Keep recent messages
        keep_recent = self.max_history_size
        recent_messages = self.conversation_history[-keep_recent:]
        
        # Summarize older messages
        old_messages = self.conversation_history[:-keep_recent]
        
        if old_messages:
            summary = {
                "role": "system",
                "content": f"[Previous conversation summary: {len(old_messages)} messages compressed]",
                "timestamp": datetime.now().isoformat(),
                "metadata": {"compressed": True, "original_count": len(old_messages)}
            }
            
            self.conversation_history = [summary] + recent_messages
    
    def update_working_directory(self, new_dir: str):
        """Update the current working directory context."""
        self.working_directory = new_dir
    
    def get_last_command_output(self) -> str:
        """Get the output of the last executed command."""
        if self.executed_commands:
            return self.executed_commands[-1]["output"]
        return ""
    
    def clear_session(self):
        """Clear all context for a fresh start."""
        self.conversation_history = []
        self.executed_commands = []
        self.session_metadata["task_count"] = 0
        self.session_metadata["last_task_status"] = None
    
    def export_context(self, filepath: str):
        """
        Export current context to a JSON file.
        
        Args:
            filepath: Path to save the context
        """
        export_data = {
            "conversation_history": self.conversation_history,
            "executed_commands": self.executed_commands,
            "working_directory": self.working_directory,
            "session_metadata": self.session_metadata
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    def import_context(self, filepath: str):
        """
        Import context from a JSON file.
        
        Args:
            filepath: Path to the context file
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.conversation_history = data.get("conversation_history", [])
        self.executed_commands = data.get("executed_commands", [])
        self.working_directory = data.get("working_directory", os.getcwd())
        self.session_metadata = data.get("session_metadata", {})
