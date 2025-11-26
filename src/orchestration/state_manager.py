"""
State Manager for the orchestration system.
Manages conversation context, execution history, and agent states.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger("cogniorch.orchestration.state")


class StateManager:
    """
    Manages state across the entire agentic system.
    Tracks conversation, execution history, agent states, and environment.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Main state components
        self.conversation_history: List[Dict[str, Any]] = []
        self.execution_history: List[Dict[str, Any]] = []
        self.agent_states: Dict[str, Any] = {}
        self.environment_state: Dict[str, Any] = {}
        self.goals: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}
        
        # Metadata
        self.session_id = self._generate_session_id()
        self.start_time = datetime.now()
        
        logger.info(f"StateManager initialized (session: {self.session_id})")
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        from uuid import uuid4
        return str(uuid4())[:8]
    
    def add_conversation_turn(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """
        Add a conversation turn.
        
        Args:
            role: Role (user/assistant/system)
            content: Message content
            metadata: Additional metadata
        """
        turn = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "metadata": metadata or {}
        }
        self.conversation_history.append(turn)
        logger.debug(f"Added conversation turn: {role}")
    
    def add_execution(self, 
                     agent: str,
                     action: str,
                     result: Any,
                     success: bool = True,
                     metadata: Dict[str, Any] = None):
        """
        Record an execution.
        
        Args:
            agent: Agent that performed the action
            action: Action performed
            result: Execution result
            success: Whether execution succeeded
            metadata: Additional metadata
        """
        execution = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "result": str(result)[:500],  # Truncate large results
            "success": success,
            "metadata": metadata or {}
        }
        self.execution_history.append(execution)
        logger.debug(f"Recorded execution: {agent} -> {action}")
    
    def update_agent_state(self, agent_name: str, state: Dict[str, Any]):
        """
        Update an agent's state.
        
        Args:
            agent_name: Name of the agent
            state: New state dictionary
        """
        self.agent_states[agent_name] = {
            "timestamp": datetime.now().isoformat(),
            "state": state
        }
        logger.debug(f"Updated state for agent: {agent_name}")
    
    def get_agent_state(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get the current state of an agent"""
        return self.agent_states.get(agent_name)
    
    def update_environment(self, key: str, value: Any):
        """
        Update environment state.
        
        Args:
            key: State key
            value: State value
        """
        self.environment_state[key] = value
        logger.debug(f"Updated environment: {key}")
    
    def get_environment(self, key: str, default: Any = None) -> Any:
        """Get environment state value"""
        return self.environment_state.get(key, default)
    
    def add_goal(self, goal: str, priority: int = 1, metadata: Dict[str, Any] = None):
        """
        Add a goal to track.
        
        Args:
            goal: Goal description
            priority: Priority level (1-10)
            metadata: Additional metadata
        """
        goal_obj = {
            "id": len(self.goals) + 1,
            "goal": goal,
            "priority": priority,
            "status": "active",
            "created": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.goals.append(goal_obj)
        logger.info(f"Added goal: {goal}")
    
    def complete_goal(self, goal_id: int):
        """Mark a goal as completed"""
        for goal in self.goals:
            if goal["id"] == goal_id:
                goal["status"] = "completed"
                goal["completed"] = datetime.now().isoformat()
                logger.info(f"Completed goal: {goal['goal']}")
                break
    
    def get_active_goals(self) -> List[Dict[str, Any]]:
        """Get all active goals"""
        return [g for g in self.goals if g["status"] == "active"]
    
    def set_context(self, key: str, value: Any):
        """Set a context value"""
        self.context[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a context value"""
        return self.context.get(key, default)
    
    def get_recent_conversation(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get the n most recent conversation turns"""
        return self.conversation_history[-n:]
    
    def get_recent_executions(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get the n most recent executions"""
        return self.execution_history[-n:]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the current state"""
        return {
            "session_id": self.session_id,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "conversation_turns": len(self.conversation_history),
            "executions": len(self.execution_history),
            "active_agents": len(self.agent_states),
            "active_goals": len(self.get_active_goals()),
            "environment_keys": list(self.environment_state.keys())
        }
    
    def export_state(self) -> Dict[str, Any]:
        """Export full state as dictionary"""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "conversation_history": self.conversation_history,
            "execution_history": self.execution_history,
            "agent_states": self.agent_states,
            "environment_state": self.environment_state,
            "goals": self.goals,
            "context": self.context
        }
    
    def save_to_file(self, filepath: str):
        """Save state to a JSON file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.export_state(), f, indent=2)
            logger.info(f"State saved to: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def load_from_file(self, filepath: str):
        """Load state from a JSON file"""
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            self.session_id = state.get("session_id", self.session_id)
            self.conversation_history = state.get("conversation_history", [])
            self.execution_history = state.get("execution_history", [])
            self.agent_states = state.get("agent_states", {})
            self.environment_state = state.get("environment_state", {})
            self.goals = state.get("goals", [])
            self.context = state.get("context", {})
            
            logger.info(f"State loaded from: {filepath}")
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
    
    def clear(self):
        """Clear all state (reset)"""
        self.conversation_history.clear()
        self.execution_history.clear()
        self.agent_states.clear()
        self.environment_state.clear()
        self.goals.clear()
        self.context.clear()
        logger.info("State cleared")
