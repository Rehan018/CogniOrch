"""
Executor Agent - Executes commands with monitoring and error recovery.
"""

from typing import Dict, Any
from ..agents.base_agent import BaseAgent, AgentRole, AgentState
from ..verification import CommandVerifier
from src.command_executor import execute_command_in_terminal, wait_for_command_completion
from src.approval_handler import ApprovalHandler
import logging
import re

logger = logging.getLogger("cogniorch.agents.executor")


class ExecutorAgent(BaseAgent):
    """
    Executor agent that runs commands with safety checks and error recovery.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(AgentRole.EXECUTOR, "ExecutorAgent", config)
        self.capabilities = ["execute", "verify", "retry"]
        self.max_retries = self.config.get("max_retries", 3)
        self.require_approval = self.config.get("require_approval", True)
        self.auto_approve = self.config.get("auto_approve", False)
    
    def process(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a command with monitoring and error recovery.
        
        Args:
            task: Task with 'command' and 'reason'
            context: Execution context
            
        Returns:
            Execution result
        """
        command = task.get("command", "")
        reason = task.get("reason", "")
        
        if not command:
            return {
                "success": False,
                "error": "No command provided",
                "executed": False
            }
        
        logger.info(f"ExecutorAgent executing: {command}")
        self.update_state(AgentState.ACTING)
        
        # Verify command safety
        is_safe, safety_reason = CommandVerifier.verify(command)
        
        if not is_safe:
            logger.warning(f"Safety check failed: {safety_reason}")
            print(f"\n\033[1;31m[SAFETY WARNING] {safety_reason}\033[0m")
            # Still allow user to approve if they want
        
        # Request approval
        approval_handler = ApprovalHandler(self.require_approval, self.auto_approve)
        approved, _ = approval_handler.request_approval(command)
        
        if not approved:
            self.update_state(AgentState.IDLE)
            return {
                "success": False,
                "error": "Command denied by user",
                "executed": False,
                "approved": False
            }
        
        # Execute with retry logic
        result = self._execute_with_retry(command)
        
        # Record execution
        self.add_to_history({
            "command": command,
            "reason": reason,
            "success": result.get("success", False),
            "output": result.get("output", "")[:200]
        })
        
        self.update_state(AgentState.IDLE)
        return result
    
    def _execute_with_retry(self, command: str) -> Dict[str, Any]:
        """Execute command with automatic retry on failure"""
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Execution attempt {attempt + 1}/{self.max_retries}")
                
                # Execute command
                temp_file = execute_command_in_terminal(command)
                if temp_file:
                    output = wait_for_command_completion(temp_file)
                    
                    # Check if execution was successful
                    success = self._check_success(output)
                    
                    if success or attempt == self.max_retries - 1:
                        return {
                            "success": success,
                            "output": output,
                            "executed": True,
                            "approved": True,
                            "attempts": attempt + 1
                        }
                    
                    # If failed and retries remain, log and continue
                    logger.warning(f"Command failed, retrying ({attempt + 1}/{self.max_retries})")
                    
                else:
                    logger.error("Failed to execute command")
                    
            except Exception as e:
                logger.error(f"Execution error: {e}")
                if attempt == self.max_retries - 1:
                    return {
                        "success": False,
                        "error": str(e),
                        "executed": False,
                        "approved": True
                    }
        
        return {
            "success": False,
            "error": "Max retries exceeded",
            "executed": False,
            "approved": True
        }
    
    def _check_success(self, output: str) -> bool:
        """
        Check if command execution was successful based on output.
        
        Args:
            output: Command output
            
        Returns:
            True if successful
        """
        # Look for common error indicators
        error_indicators = [
            "error:",
            "failed",
            "permission denied",
            "command not found",
            "no such file",
            "cannot"
        ]
        
        output_lower = output.lower()
        
        # Check for error indicators
        for indicator in error_indicators:
            if indicator in output_lower:
                return False
        
        # Check exit code if present
        exit_code_match = re.search(r"exit code:\s*(\d+)", output_lower)
        if exit_code_match:
            exit_code = int(exit_code_match.group(1))
            return exit_code == 0
        
        # If no errors found, assume success
        return True
