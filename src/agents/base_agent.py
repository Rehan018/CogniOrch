"""
Base Agent class for the Multi-Agent System.
All specialized agents inherit from this base.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
import logging

logger = logging.getLogger("cogniorch.agents")


class AgentRole(Enum):
    """Agent role definitions"""
    PLANNER = "planner"
    EXECUTOR = "executor"
    VERIFIER = "verifier"
    DEBUGGER = "debugger"
    OPTIMIZER = "optimizer"
    COORDINATOR = "coordinator"


class AgentState(Enum):
    """Agent state definitions"""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING = "waiting"
    ERROR = "error"


class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, role: AgentRole, name: str, config: Dict[str, Any] = None):
        """
        Initialize base agent.
        
        Args:
            role: The role of this agent
            name: Human-readable name
            config: Configuration dictionary
        """
        self.role = role
        self.name = name
        self.config = config or {}
        self.state = AgentState.IDLE
        self.history: List[Dict[str, Any]] = []
        self.capabilities: List[str] = []
        
        logger.info(f"Initialized {self.name} ({self.role.value})")
    
    @abstractmethod
    def process(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a task given context.
        
        Args:
            task: Task specification
            context: Current context including state and history
            
        Returns:
            Result dictionary with output and metadata
        """
        pass
    
    def can_handle(self, task: Dict[str, Any]) -> bool:
        """
        Check if this agent can handle the given task.
        
        Args:
            task: Task specification
            
        Returns:
            True if agent can handle the task
        """
        task_type = task.get("type", "")
        return task_type in self.capabilities
    
    def update_state(self, new_state: AgentState):
        """Update agent state"""
        logger.debug(f"{self.name} state: {self.state.value} -> {new_state.value}")
        self.state = new_state
    
    def add_to_history(self, entry: Dict[str, Any]):
        """Add entry to agent's execution history"""
        self.history.append(entry)
        
        # Keep history manageable
        if len(self.history) > 100:
            self.history = self.history[-50:]
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "name": self.name,
            "role": self.role.value,
            "state": self.state.value,
            "capabilities": self.capabilities,
            "history_length": len(self.history)
        }
