"""
RAG (Retrieval Augmented Generation) Knowledge Base.
Stores and retrieves context for enhanced AI responses.
"""

from typing import List, Dict, Any, Optional
import json
import os
from datetime import datetime
import logging

logger = logging.getLogger("cogniorch.rag.knowledge")


class KnowledgeEntry:
    """Represents a single knowledge entry"""
    
    def __init__(self, 
                 content: str,
                 category: str,
                 metadata: Dict[str, Any] = None,
                 tags: List[str] = None):
        self.id = self._generate_id()
        self.content = content
        self.category = category
        self.metadata = metadata or {}
        self.tags = tags or []
        self.created = datetime.now().isoformat()
        self.access_count = 0
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        from uuid import uuid4
        return str(uuid4())[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "content": self.content,
            "category": self.category,
            "metadata": self.metadata,
            "tags": self.tags,
            "created": self.created,
            "access_count": self.access_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeEntry':
        """Create from dictionary"""
        entry = cls(
            content=data["content"],
            category=data["category"],
            metadata=data.get("metadata", {}),
            tags=data.get("tags", [])
        )
        entry.id = data.get("id", entry.id)
        entry.created = data.get("created", entry.created)
        entry.access_count = data.get("access_count", 0)
        return entry


class KnowledgeBase:
    """
    Knowledge base for storing and retrieving contextual information.
    Supports command history, system information, and learned patterns.
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.expanduser("~/.cogniorch/knowledge_base.json")
        self.entries: Dict[str, KnowledgeEntry] = {}
        self.categories = {
            "command": [],
            "system_info": [],
            "error_pattern": [],
            "solution": [],
            "tip": [],
            "documentation": []
        }
        
        # Ensure storage directory exists
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        
        # Load existing knowledge
        self.load()
        
        logger.info(f"KnowledgeBase initialized with {len(self.entries)} entries")
    
    def add(self, 
            content: str,
            category: str,
            metadata: Dict[str, Any] = None,
            tags: List[str] = None) -> str:
        """
        Add a knowledge entry.
        
        Args:
            content: Entry content
            category: Entry category
            metadata: Additional metadata
            tags: Tags for categorization
            
        Returns:
            Entry ID
        """
        entry = KnowledgeEntry(content, category, metadata, tags)
        self.entries[entry.id] = entry
        
        if category in self.categories:
            self.categories[category].append(entry.id)
        
        logger.debug(f"Added knowledge entry: {entry.id} ({category})")
        
        # Auto-save
        self.save()
        
        return entry.id
    
    def get(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Get an entry by ID"""
        entry = self.entries.get(entry_id)
        if entry:
            entry.access_count += 1
        return entry
    
    def search(self, 
               query: str = None,
               category: str = None,
               tags: List[str] = None,
               limit: int = 10) -> List[KnowledgeEntry]:
        """
        Search for knowledge entries.
        
        Args:
            query: Text to search for
            category: Filter by category
            tags: Filter by tags
            limit: Maximum results
            
        Returns:
            List of matching entries
        """
        results = []
        
        for entry in self.entries.values():
            # Category filter
            if category and entry.category != category:
                continue
            
            # Tag filter
            if tags and not any(tag in entry.tags for tag in tags):
                continue
            
            # Query filter (simple substring match)
            if query and query.lower() not in entry.content.lower():
                continue
            
            results.append(entry)
            
            if len(results) >= limit:
                break
        
        # Sort by access count (most used first)
        results.sort(key=lambda e: e.access_count, reverse=True)
        
        return results
    
    def add_command_execution(self, 
                             command: str,
                             output: str,
                             success: bool,
                             context: Dict[str, Any] = None):
        """
        Record a command execution for future reference.
        
        Args:
            command: Command executed
            output: Command output
            success: Whether command succeeded
            context: Execution context
        """
        content = f"Command: {command}\nResult: {output[:200]}"
        
        self.add(
            content=content,
            category="command",
            metadata={
                "command": command,
                "success": success,
                "context": context or {}
            },
            tags=["execution", "success" if success else "failure"]
        )
    
    def add_error_pattern(self,
                         error: str,
                         solution: str,
                         context: Dict[str, Any] = None):
        """
        Record an error pattern and its solution.
        
        Args:
            error: Error message
            solution: Solution that worked
            context: Error context
        """
        content = f"Error: {error}\nSolution: {solution}"
        
        self.add(
            content=content,
            category="error_pattern",
            metadata={
                "error": error,
                "solution": solution,
                "context": context or {}
            },
            tags=["error", "solution"]
        )
    
    def get_similar_commands(self, command: str, limit: int = 5) -> List[KnowledgeEntry]:
        """
        Find similar command executions.
        
        Args:
            command: Command to match
            limit: Maximum results
            
        Returns:
            Similar command entries
        """
        # Extract key words from command
        keywords = command.split()[:3]  # First few words
        
        results = []
        for entry in self.entries.values():
            if entry.category != "command":
                continue
            
            # Simple similarity check
            if any(kw in entry.content for kw in keywords):
                results.append(entry)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_context_for_query(self, query: str, max_entries: int = 5) -> str:
        """
        Get relevant context for a query.
        
        Args:
            query: User query
            max_entries: Maximum context entries
            
        Returns:
            Formatted context string
        """
        # Search for relevant entries
        results = self.search(query=query, limit=max_entries)
        
        if not results:
            return ""
        
        context_parts = ["=== Relevant Context ==="]
        for entry in results:
            context_parts.append(f"\n[{entry.category}] {entry.content[:150]}...")
        
        return "\n".join(context_parts)
    
    def save(self):
        """Save knowledge base to file"""
        try:
            data = {
                "entries": {
                    eid: entry.to_dict() 
                    for eid, entry in self.entries.items()
                },
                "categories": self.categories
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Knowledge base saved to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save knowledge base: {e}")
    
    def load(self):
        """Load knowledge base from file"""
        if not os.path.exists(self.storage_path):
            logger.debug("No existing knowledge base found, starting fresh")
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            self.entries = {
                eid: KnowledgeEntry.from_dict(edata)
                for eid, edata in data.get("entries", {}).items()
            }
            
            self.categories = data.get("categories", self.categories)
            
            logger.info(f"Loaded {len(self.entries)} knowledge entries")
        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}")
    
    def clear(self):
        """Clear all entries"""
        self.entries.clear()
        for category in self.categories:
            self.categories[category].clear()
        self.save()
        logger.info("Knowledge base cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        return {
            "total_entries": len(self.entries),
            "categories": {
                cat: len(entries)
                for cat, entries in self.categories.items()
            },
            "storage_path": self.storage_path
        }


# Global knowledge base instance
knowledge_base = KnowledgeBase()
