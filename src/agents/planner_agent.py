"""
Planner Agent - Creates execution plans using hierarchical planning.
"""

from typing import Dict, Any, List
from ..agents.base_agent import BaseAgent, AgentRole, AgentState
import logging

logger = logging.getLogger("cogniorch.agents.planner")


class PlanStep:
    """Represents a single step in an execution plan"""
    
    def __init__(self, step_id: int, action: str, rationale: str, dependencies: List[int] = None):
        self.step_id = step_id
        self.action = action
        self.rationale = rationale
        self.dependencies = dependencies or []
        self.status = "pending"  # pending, in_progress, completed, failed
        self.result = None
    
    def __str__(self):
        return f"Step {self.step_id}: {self.action} ({self.status})"


class ExecutionPlan:
    """Represents a complete execution plan"""
    
    def __init__(self, goal: str, steps: List[PlanStep]):
        self.goal = goal
        self.steps = steps
        self.current_step = 0
    
    def get_next_step(self) -> PlanStep:
        """Get the next executable step"""
        for step in self.steps:
            if step.status == "pending":
                # Check if dependencies are met
                if all(self.steps[dep - 1].status == "completed" for dep in step.dependencies):
                    return step
        return None
    
    def mark_complete(self, step_id: int, result: Any = None):
        """Mark a step as completed"""
        for step in self.steps:
            if step.step_id == step_id:
                step.status = "completed"
                step.result = result
                break
    
    def mark_failed(self, step_id: int, error: str):
        """Mark a step as failed"""
        for step in self.steps:
            if step.step_id == step_id:
                step.status = "failed"
                step.result = error
                break
    
    def is_complete(self) -> bool:
        """Check if all steps are completed"""
        return all(step.status == "completed" for step in self.steps)
    
    def get_progress(self) -> float:
        """Get completion percentage"""
        if not self.steps:
            return 0.0
        completed = sum(1 for step in self.steps if step.status == "completed")
        return (completed / len(self.steps)) * 100


class PlannerAgent(BaseAgent):
    """
    Planning agent responsible for creating execution plans.
    Uses hierarchical task decomposition.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(AgentRole.PLANNER, "PlannerAgent", config)
        self.capabilities = ["plan", "decompose", "strategy"]
        self.max_steps = self.config.get("max_plan_steps", 10)
    
    def process(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an execution plan for the task.
        
        Args:
            task: Task specification with 'goal' and 'constraints'
            context: Current context
            
        Returns:
            Execution plan
        """
        self.update_state(AgentState.THINKING)
        
        goal = task.get("goal", "")
        constraints = task.get("constraints", {})
        
        logger.info(f"PlannerAgent creating plan for: {goal}")
        
        # Decompose goal into steps
        plan_steps = self._decompose_goal(goal, constraints, context)
        
        # Create execution plan
        plan = ExecutionPlan(goal, plan_steps)
        
        # Record in history
        self.add_to_history({
            "goal": goal,
            "steps": len(plan_steps),
            "plan": [str(step) for step in plan_steps]
        })
        
        self.update_state(AgentState.IDLE)
        
        return {
            "success": True,
            "plan": plan,
            "steps": plan_steps
        }
    
    def _decompose_goal(self, goal: str, constraints: Dict[str, Any], context: Dict[str, Any]) -> List[PlanStep]:
        """
        Decompose a goal into executable steps.
        This is where the actual planning logic would use LLM or planning algorithms.
        
        Args:
            goal: The goal to achieve
            constraints: Constraints on the plan
            context: Current context
            
        Returns:
            List of plan steps
        """
        # This is a template implementation
        # In production, this would use:
        # 1. LLM-based decomposition
        # 2. Hierarchical Task Network (HTN) planning
        # 3. STRIPS-like planning
        
        steps = []
        
        # Example decomposition logic
        # This should be replaced with actual LLM-driven planning
        
        if "install" in goal.lower():
            steps.append(PlanStep(1, "verify_system_info", "Check OS and package manager"))
            steps.append(PlanStep(2, "search_package", "Find the package", [1]))
            steps.append(PlanStep(3, "install_package", "Install the package", [2]))
            steps.append(PlanStep(4, "verify_installation", "Verify installation", [3]))
        
        elif "file" in goal.lower() and "create" in goal.lower():
            steps.append(PlanStep(1, "check_path", "Verify target path exists"))
            steps.append(PlanStep(2, "create_file", "Create the file", [1]))
            steps.append(PlanStep(3, "verify_file", "Verify file creation", [2]))
        
        elif "analyze" in goal.lower() or "check" in goal.lower():
            steps.append(PlanStep(1, "gather_info", "Collect system information"))
            steps.append(PlanStep(2, "analyze_data", "Analyze the data", [1]))
            steps.append(PlanStep(3, "generate_report", "Create report", [2]))
        
        else:
            # Generic plan
            steps.append(PlanStep(1, "analyze_request", "Understand the request"))
            steps.append(PlanStep(2, "gather_context", "Collect necessary information", [1]))
            steps.append(PlanStep(3, "execute_action", "Perform the action", [2]))
            steps.append(PlanStep(4, "verify_result", "Verify the outcome", [3]))
        
        logger.debug(f"Generated {len(steps)} steps for goal: {goal}")
        return steps
    
    def refine_plan(self, plan: ExecutionPlan, feedback: str) -> ExecutionPlan:
        """
        Refine an existing plan based on feedback.
        
        Args:
            plan: Current execution plan
            feedback: Feedback on the plan
            
        Returns:
            Refined execution plan
        """
        # This would use LLM to refine the plan based on feedback
        logger.info(f"Refining plan based on feedback: {feedback[:50]}...")
        return plan
    
    def estimate_complexity(self, plan: ExecutionPlan) -> str:
        """
        Estimate the complexity of a plan.
        
        Args:
            plan: Execution plan
            
        Returns:
            Complexity level (low/medium/high)
        """
        step_count = len(plan.steps)
        
        if step_count <= 3:
            return "low"
        elif step_count <= 6:
            return "medium"
        else:
            return "high"
