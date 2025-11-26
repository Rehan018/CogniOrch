"""
Main Orchestrator - Coordinates all agents and manages workflow.
"""

from typing import Dict, Any, Optional, List
from ..agents.base_agent import BaseAgent, AgentState
from ..agents.planner_agent import PlannerAgent, ExecutionPlan
from ..reasoning.cot_engine import CoTEngine
from ..reasoning.react_engine import ReActEngine
from ..orchestration.state_manager import StateManager
from ..tools.tool_registry import registry
import logging

logger = logging.getLogger("cogniorch.orchestrator")


class Orchestrator:
    """
    Main orchestrator that coordinates the entire agentic system.
    Manages agents, reasoning engines, and workflow execution.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize components
        self.state_manager = StateManager(config.get("state", {}))
        self.cot_engine = CoTEngine(config.get("cot", {}))
        self.react_engine = ReActEngine(config.get("react", {}))
        
        # Initialize agents
        self.agents: Dict[str, BaseAgent] = {}
        self._initialize_agents()
        
        # Configuration
        self.use_cot = self.config.get("use_cot", True)
        self.use_react = self.config.get("use_react", True)
        self.use_planning = self.config.get("use_planning", True)
        
        logger.info("Orchestrator initialized")
    
    def _initialize_agents(self):
        """Initialize all agents"""
        # Planner agent
        self.agents["planner"] = PlannerAgent(self.config.get("planner", {}))
        
        logger.info(f"Initialized {len(self.agents)} agents")
    
    def process_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a user query through the agentic system.
        
        Args:
            query: User query
            context: Additional context
            
        Returns:
            Result dictionary
        """
        logger.info(f"Processing query: {query[:50]}...")
        
        # Add to state
        self.state_manager.add_conversation_turn("user", query)
        self.state_manager.add_goal(query)
        
        context = context or {}
        context.update(self.state_manager.get_context("global", {}))
        
        # Determine processing strategy
        complexity = self._assess_complexity(query)
        logger.debug(f"Query complexity: {complexity}")
        
        result = {}
        
        try:
            if complexity == "high" and self.use_planning:
                # Use full planning pipeline
                result = self._process_with_planning(query, context)
            
            elif self.use_react:
                # Use ReAct loop
                result = self._process_with_react(query, context)
            
            elif self.use_cot:
                # Use Chain of Thought
                result = self._process_with_cot(query, context)
            
            else:
                # Direct processing
                result = self._process_direct(query, context)
            
            # Record result
            self.state_manager.add_conversation_turn(
                "assistant",
                str(result.get("response", "")),
                {"complexity": complexity}
            )
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            import traceback
            traceback.print_exc()
            result = {
                "success": False,
                "error": str(e),
                "response": f"I encountered an error: {str(e)}"
            }
        
        return result
    
    def _assess_complexity(self, query: str) -> str:
        """
        Assess the complexity of a query.
        
        Args:
            query: User query
            
        Returns:
            Complexity level (low/medium/high)
        """
        # Simple heuristics - in production use LLM
        query_lower = query.lower()
        
        # High complexity indicators
        high_indicators = [
            "install and configure",
            "debug",
            "analyze and fix",
            "setup",
            "deploy",
            "multiple",
            "and then"
        ]
        
        # Low complexity indicators
        low_indicators = [
            "what is",
            "when is",
            "show me",
            "list",
            "display"
        ]
        
        if any(ind in query_lower for ind in high_indicators):
            return "high"
        elif any(ind in query_lower for ind in low_indicators):
            return "low"
        else:
            return "medium"
    
    def _process_with_planning(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process query using full planning pipeline"""
        logger.info("Using planning pipeline")
        
        # Generate Chain of Thought
        if self.use_cot:
            self.cot_engine.think(query, context)
            context["cot"] = self.cot_engine.format_for_display()
        
        # Create execution plan
        planner = self.agents["planner"]
        plan_result = planner.process({"goal": query}, context)
        
        if not plan_result.get("success"):
            return {"success": False, "response": "Failed to create plan"}
        
        plan: ExecutionPlan = plan_result["plan"]
        
        # Execute plan steps
        execution_results = []
        while not plan.is_complete():
            next_step = plan.get_next_step()
            if not next_step:
                break
            
            logger.info(f"Executing: {next_step}")
            
            # Execute step (simplified - would use executor agent)
            step_result = self._execute_plan_step(next_step, context)
            execution_results.append(step_result)
            
            if step_result.get("success"):
                plan.mark_complete(next_step.step_id, step_result)
            else:
                plan.mark_failed(next_step.step_id, step_result.get("error", "Unknown error"))
                break
        
        # Compile response
        response = self._compile_response(plan, execution_results, context)
        
        return {
            "success": plan.is_complete(),
            "plan": plan,
            "execution_results": execution_results,
            "response": response
        }
    
    def _process_with_react(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process query using ReAct loop"""
        logger.info("Using ReAct loop")
        
        # Register tools for ReAct
        self._register_react_tools()
        
        # Run ReAct loop
        result = self.react_engine.run(
            goal=query,
            context=context
        )
        
        response = self.react_engine.format_trace()
        
        return {
            "success": result.get("success", False),
            "trace": result.get("trace", []),
            "response": response
        }
    
    def _process_with_cot(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process query using Chain of Thought"""
        logger.info("Using Chain of Thought")
        
        # Generate reasoning chain
        self.cot_engine.think(query, context)
        
        # Get conclusion and execute if needed
        conclusion = self.cot_engine.get_conclusion()
        
        response = self.cot_engine.format_for_display(show_reasoning=True)
        
        return {
            "success": True,
            "reasoning": self.cot_engine.current_chain,
            "conclusion": conclusion,
            "response": response
        }
    
    def _process_direct(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Direct processing without complex reasoning"""
        logger.info("Using direct processing")
        
        # Simple direct execution
        response = f"Processing: {query}"
        
        return {
            "success": True,
            "response": response
        }
    
    def _execute_plan_step(self, step, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single plan step"""
        # This would use the executor agent and tool registry
        # For now, simplified
        
        try:
            # Record execution
            self.state_manager.add_execution(
                agent="executor",
                action=step.action,
                result="Simulated execution",
                success=True
            )
            
            return {
                "success": True,
                "result": f"Executed: {step.action}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _register_react_tools(self):
        """Register tools for ReAct engine"""
        # Register some basic tools
        self.react_engine.register_tool("execute_command", lambda cmd, ctx: f"Executed: {cmd}")
        self.react_engine.register_tool("get_info", lambda param, ctx: "Information retrieved")
    
    def _compile_response(self, plan: ExecutionPlan, results: List[Dict], context: Dict) -> str:
        """Compile a final response from plan execution"""
        lines = [f"📋 Executed plan for: {plan.goal}"]
        lines.append(f"Progress: {plan.get_progress():.0f}%")
        lines.append("")
        
        for i, step in enumerate(plan.steps, 1):
            status_icon = "✓" if step.status == "completed" else "✗" if step.status == "failed" else "⋯"
            lines.append(f"{status_icon} Step {i}: {step.action}")
        
        return "\n".join(lines)
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return {
            "state": self.state_manager.get_summary(),
            "agents": {name: agent.get_status() for name, agent in self.agents.items()},
            "config": {
                "use_cot": self.use_cot,
                "use_react": self.use_react,
                "use_planning": self.use_planning
            }
        }
