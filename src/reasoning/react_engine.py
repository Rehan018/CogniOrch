"""
ReAct (Reasoning + Acting) engine.
Implements the ReAct pattern: Thought → Action → Observation loop.
"""

from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import logging

logger = logging.getLogger("cogniorch.reasoning.react")


class ReActStepType(Enum):
    """Types of steps in the ReAct loop"""
    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"


class ReActStep:
    """Represents a single step in the ReAct loop"""
    
    def __init__(self, step_type: ReActStepType, content: str, metadata: Dict[str, Any] = None):
        self.step_type = step_type
        self.content = content
        self.metadata = metadata or {}
    
    def __str__(self):
        prefix = {
            ReActStepType.THOUGHT: "💭 Thought",
            ReActStepType.ACTION: "⚡ Action",
            ReActStepType.OBSERVATION: "👁️  Observation"
        }
        return f"{prefix[self.step_type]}: {self.content}"


class ReActEngine:
    """
    ReAct (Reasoning + Acting) engine.
    Implements the pattern of interleaving reasoning and action.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.max_iterations = self.config.get("max_iterations", 10)
        self.verbose = self.config.get("verbose", True)
        self.trace: List[ReActStep] = []
        self.tools: Dict[str, Callable] = {}
    
    def register_tool(self, name: str, func: Callable):
        """Register a tool (action) that can be called"""
        self.tools[name] = func
        logger.debug(f"ReAct: Registered tool '{name}'")
    
    def run(self, 
            goal: str, 
            context: Dict[str, Any] = None,
            llm_think: Callable = None,
            llm_act: Callable = None) -> Dict[str, Any]:
        """
        Run the ReAct loop.
        
        Args:
            goal: The goal to achieve
            context: Initial context
            llm_think: Function to generate thoughts (LLM call)
            llm_act: Function to decide on actions (LLM call)
            
        Returns:
            Result dictionary with final answer and trace
        """
        self.trace = []
        context = context or {}
        iteration = 0
        
        logger.info(f"ReAct: Starting loop for goal: {goal[:50]}...")
        
        while iteration < self.max_iterations:
            iteration += 1
            
            # THOUGHT phase
            thought = self._think(goal, context, llm_think)
            self._add_step(ReActStepType.THOUGHT, thought)
            
            # Check if we're done
            if self._is_goal_achieved(thought, goal):
                logger.info(f"ReAct: Goal achieved in {iteration} iterations")
                break
            
            # ACTION phase
            action = self._decide_action(thought, context, llm_act)
            self._add_step(ReActStepType.ACTION, action)
            
            # Execute action and get observation
            observation = self._execute_action(action, context)
            self._add_step(ReActStepType.OBSERVATION, observation)
            
            # Update context with observation
            context["last_observation"] = observation
            context["iteration"] = iteration
        
        return {
            "success": iteration < self.max_iterations,
            "iterations": iteration,
            "trace": self.trace,
            "final_context": context
        }
    
    def _think(self, goal: str, context: Dict[str, Any], llm_think: Callable = None) -> str:
        """
        Generate a thought based on current state.
        
        Args:
            goal: The goal to achieve
            context: Current context
            llm_think: Optional LLM function for thinking
            
        Returns:
            Thought string
        """
        if llm_think:
            return llm_think(goal, context)
        
        # Default thinking logic (template)
        last_obs = context.get("last_observation", "")
        if last_obs:
            return f"Based on observation '{last_obs}', I need to continue toward: {goal}"
        else:
            return f"I need to achieve: {goal}. Let me start by analyzing the situation."
    
    def _decide_action(self, thought: str, context: Dict[str, Any], llm_act: Callable = None) -> str:
        """
        Decide on an action based on the thought.
        
        Args:
            thought: Current thought
            context: Current context
            llm_act: Optional LLM function for action selection
            
        Returns:
            Action string
        """
        if llm_act:
            return llm_act(thought, context, list(self.tools.keys()))
        
        # Default action selection (template)
        return "execute_command"
    
    def _execute_action(self, action: str, context: Dict[str, Any]) -> str:
        """
        Execute an action and return observation.
        
        Args:
            action: Action to execute
            context: Current context
            
        Returns:
            Observation string
        """
        # Parse action (format: "tool_name:params")
        parts = action.split(":", 1)
        tool_name = parts[0].strip()
        params = parts[1].strip() if len(parts) > 1 else ""
        
        if tool_name in self.tools:
            try:
                result = self.tools[tool_name](params, context)
                return f"Action '{tool_name}' completed: {result}"
            except Exception as e:
                return f"Action '{tool_name}' failed: {str(e)}"
        else:
            return f"Unknown action: {tool_name}"
    
    def _is_goal_achieved(self, thought: str, goal: str) -> bool:
        """
        Check if the goal has been achieved.
        
        Args:
            thought: Current thought
            goal: Original goal
            
        Returns:
            True if goal is achieved
        """
        # Simple heuristic - in production, use LLM to evaluate
        done_indicators = ["completed", "finished", "done", "achieved", "success"]
        thought_lower = thought.lower()
        return any(indicator in thought_lower for indicator in done_indicators)
    
    def _add_step(self, step_type: ReActStepType, content: str):
        """Add a step to the trace"""
        step = ReActStep(step_type, content)
        self.trace.append(step)
        
        if self.verbose:
            logger.debug(str(step))
    
    def format_trace(self) -> str:
        """Format the execution trace for display"""
        if not self.trace:
            return "No trace available."
        
        output = ["📋 ReAct Trace:"]
        for i, step in enumerate(self.trace, 1):
            output.append(f"\n{i}. {step}")
        
        return "\n".join(output)
    
    def clear(self):
        """Clear the execution trace"""
        self.trace = []
