import httpx
import jwt
import json
import logging
import os
import time
import re
from src.command_executor import execute_command_in_terminal, execute_command
from src.utils import load_persistent_memory
from src.mcp_protocol import mcp
import openai
from src.token_manager import TokenManager
from src.command_executor import wait_for_command_completion
from src.approval_handler import ApprovalHandler

# Import agentic components
from src.orchestration.orchestrator import Orchestrator
from src.agents.executor_agent import ExecutorAgent
from src.rag.knowledge_base import knowledge_base

# Clear all proxy environment variables
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('all_proxy', None)
os.environ.pop('ALL_PROXY', None)
os.environ.pop('socks_proxy', None)
os.environ.pop('SOCKS_PROXY', None)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("cogniorch.ai_core")


class CogniOrchAI:
    def __init__(self, config):
        self.mode = config.get('mode', 'ollama')
        logger.info(f"Initializing CogniOrchAI in {self.mode} mode.")
        self.require_approval = config.get('command_approval', {}).get('require_approval', True)
        self.auto_approve_all = config.get('command_approval', {}).get('auto_approve_all', False)
        self.is_streaming_mode = config.get('stream', True)
        self.config = config

        if self.mode == 'digital_ocean':
            self.token_manager = TokenManager(
                agent_id=config['digital_ocean_config']['agent_id'],
                agent_key=config['digital_ocean_config']['agent_key'],
                auth_api_url="https://cluster-api.do-ai.run/v1"
            )
            self.access_token = self.token_manager.get_valid_access_token()
            self.token_timestamp = time.time()
            self.agent_endpoint = config['digital_ocean_config']['agent_endpoint']
            self.model = config['digital_ocean_config']['model']
        else:
            openai.api_base = config['api_url']
            openai.api_key = config['api_key']
            self.model = config['model']

        self.ollama_config = config.get('ollama_config', {})
        self.history = []
        self.context_initialized = False
        
        # Initialize agentic components
        self.use_agentic_mode = config.get('use_agentic_mode', True)
        if self.use_agentic_mode:
            logger.info("Initializing agentic components...")
            orchestrator_config = {
                "use_cot": True,
                "use_react": False,  # We'll handle ReAct manually
                "use_planning": True,
                "executor": {
                    "require_approval": self.require_approval,
                    "auto_approve": self.auto_approve_all,
                    "max_retries": 2
                }
            }
            self.orchestrator = Orchestrator(orchestrator_config)
            self.executor_agent = ExecutorAgent(orchestrator_config.get("executor", {}))
            logger.info("Agentic components initialized")

    def _ensure_valid_token(self):
        """Check that the token is still valid and renew it if necessary"""
        if self.mode != 'digital_ocean':
            return

        current_time = time.time()
        token_age = current_time - self.token_timestamp

        if token_age > 900:  # 15 minutes
            try:
                logger.info("Token age > 15 minutes, refreshing...")
                self.access_token = self.token_manager.get_valid_access_token()
                self.token_timestamp = current_time
            except Exception as e:
                logger.error(f"Error refreshing token: {e}")
                self.token_manager = TokenManager(
                    agent_id=self.config['digital_ocean_config']['agent_id'],
                    agent_key=self.config['digital_ocean_config']['agent_key'],
                    auth_api_url="https://cluster-api.do-ai.run/v1"
                )
                self.access_token = self.token_manager.get_valid_access_token()
                self.token_timestamp = current_time

    def initialize_context(self):
        # We'll use a cleaner context initialization that doesn't force commands to be run visible
        context_data = load_persistent_memory()
        
        system_instructions = """
SYSTEM INSTRUCTIONS - FOLLOW STRICTLY:
You are CogniOrch, an advanced AI terminal assistant.

CRITICAL RULES FOR COMMAND GENERATION:
1. **NO UNNECESSARY COMMANDS**: Do NOT generate commands like `pwd`, `ls`, `uname`, or `whoami` unless the user explicitly asks for system information.
2. **CONVERSATIONAL FIRST**: If the user asks "who are you", "what can you do", or "hi", ANSWER WITH TEXT ONLY. Do not execute a command to "prove" you are a terminal.
3. **EXPLICIT INTENT**: Only generate `<mcp:terminal>` tags when the user's request clearly requires interaction with the OS (e.g., "install", "list files", "check memory", "run script").
4. **ONE COMMAND AT A TIME**: If a command is needed, output exactly one.

AGENTIC WORKFLOW:
- User: "who are you?"
- You: [TEXT ONLY] I am CogniOrch, a terminal assistant... (STOP, NO COMMANDS)

- User: "what system is this?"
- You: Let me check the system details.
- <mcp:terminal>uname -a</mcp:terminal>

- User: "create a file"
- You: I'll create that file for you.
- <mcp:terminal>touch filename</mcp:terminal>

FORBIDDEN BEHAVIORS:
❌ User: "who are you" -> You: <mcp:terminal>uname -a</mcp:terminal> (WRONG!)
❌ User: "hi" -> You: <mcp:terminal>ls -la</mcp:terminal> (WRONG!)

Remember: You are helpful and intelligent. You don't need to run commands to show you exist.
"""
        full_context = f"{system_instructions}\n\n{context_data}\n\n</context>"
        self.context_initialized = True
        return full_context

    def _query_ollama(self, prompt, clear_thinking=False):
        """Query Ollama API for completions."""
        messages = self.history.copy()
        messages.append({"role": "user", "content": prompt})

        try:
            import requests
            
            # Ollama API endpoint
            api_url = self.ollama_config.get('api_url', 'http://localhost:11434')
            
            # Prepare payload for Ollama
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": self.is_streaming_mode,
            }

            full_response = ""
            is_first_chunk = True

            if self.is_streaming_mode:
                # Streaming mode
                response = requests.post(
                    f"{api_url}/api/chat",
                    json=payload,
                    stream=True,
                    timeout=30
                )
                response.raise_for_status()

                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            if 'message' in chunk and 'content' in chunk['message']:
                                content = chunk['message']['content']
                                if content:
                                    if is_first_chunk:
                                        if clear_thinking:
                                            print('\r' + ' ' * 30 + '\r', end="", flush=True)
                                        print("\033[1;34mCogniOrch:\033[0m ", end='', flush=True)
                                        is_first_chunk = False

                                    print(content, end='', flush=True)
                                    full_response += content
                                    
                            # Check if done
                            if chunk.get('done', False):
                                break
                        except json.JSONDecodeError:
                            continue
            else:
                # Non-streaming mode
                payload['stream'] = False
                response = requests.post(
                    f"{api_url}/api/chat",
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
                
                if 'message' in result and 'content' in result['message']:
                    full_response = result['message']['content']
                    if clear_thinking:
                        print('\r' + ' ' * 30 + '\r', end="", flush=True)
                    print("\033[1;34mCogniOrch:\033[0m ", end='', flush=True)
                    print(full_response, end='', flush=True)

            print()
            return full_response  # Return raw response, processing happens in query()

        except requests.exceptions.ConnectionError:
            print("Error: Cannot connect to Ollama. Make sure Ollama is running (ollama serve).")
            return "An error occurred: Cannot connect to Ollama. Please ensure Ollama is running."
        except requests.exceptions.Timeout:
            print("Error: Ollama request timed out.")
            return "An error occurred: Request timed out."
        except Exception as e:
            print(f"Error while querying Ollama: {e}")
            return "An error occurred while querying Ollama."

    def _query_digitalocean(self, prompt, clear_thinking=False):
        self._ensure_valid_token()

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": self.history + [{"role": "user", "content": prompt}],
            "stream": True,
        }

        max_retries = 2
        retry_count = 0

        while retry_count < max_retries:
            try:
                with httpx.stream(
                        "POST",
                        f"{self.agent_endpoint}/chat/completions",
                        json=payload,
                        headers=headers,
                        timeout=30.0
                ) as response:
                    response.raise_for_status()

                    is_first_chunk = True
                    assistant_response = ""

                    for line in response.iter_lines():
                        line = line.strip()
                        if line.startswith("data:"):
                            line = line[len("data:"):].strip()

                        if line:
                            try:
                                chunk = json.loads(line)
                                if "choices" in chunk and chunk["choices"]:
                                    content = chunk["choices"][0].get("delta", {}).get("content", "")
                                    if content:
                                        if is_first_chunk:
                                            if clear_thinking:
                                                print('\r' + ' ' * 30 + '\r', end="", flush=True)
                                            print("\033[1;34mCogniOrch:\033[0m ", end="", flush=True)
                                            is_first_chunk = False
                                        print(content, end="", flush=True)
                                        assistant_response += content
                            except json.JSONDecodeError:
                                if line == "[DONE]":
                                    break
                                continue
                    print()

                    if assistant_response.strip():
                        return assistant_response.strip()  # Return raw response
                    return ""

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401 and retry_count < max_retries:
                    retry_count += 1
                    self.token_manager = TokenManager(
                        agent_id=self.config['digital_ocean_config']['agent_id'],
                        agent_key=self.config['digital_ocean_config']['agent_key'],
                        auth_api_url="https://cluster-api.do-ai.run/v1"
                    )
                    self.access_token = self.token_manager.get_valid_access_token()
                    self.token_timestamp = time.time()
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    continue
                else:
                    print(f"Details: {e}")
                    break

            except httpx.ReadTimeout:
                retry_count += 1
                if retry_count < max_retries:
                    self.access_token = self.token_manager.get_valid_access_token()
                    self.token_timestamp = time.time()
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    continue
                else:
                    print("Failed after multiple attempts.")
                    break

            except Exception as e:
                import traceback
                print(f"\nDetailed error: {e}")
                print(traceback.format_exc())
                break

        return "Sorry, I couldn't get a response. Please try again."
    
    def _extract_first_command(self, response_text):
        """
        Extract the first MCP command from the response.
        Returns: (command, protocol) or (None, None)
        """
        # Match <mcp:protocol>command</mcp:protocol> tags
        pattern = r'<mcp:(\w+)>(.*?)</mcp:\1>'
        match = re.search(pattern, response_text, re.DOTALL)
        
        if match:
            protocol = match.group(1)
            command = match.group(2).strip()
            return command, protocol
        
        return None, None

    def query(self, prompt, clear_thinking=False):
        """
        Main query method with intelligent routing.
        Routes to simple loop for single commands or full planning for complex tasks.
        """
        try:
            if not self.context_initialized:
                context = self.initialize_context()
                prompt = f"{context}\n\n{prompt}"

            # Analyze task complexity
            complexity = self._assess_task_complexity(prompt)
            
            if complexity == "high" and self.use_agentic_mode:
                # Use full planning/CoT/ReAct system
                logger.info("Using full agentic planning mode")
                return self._query_with_planning(prompt, clear_thinking)
            else:
                # Use simple agentic loop (fast for single commands)
                logger.info("Using simple agentic loop")
                return self._query_simple(prompt, clear_thinking)
            
        except Exception as e:
            import traceback
            logger.error(f"Query error: {e}")
            print(f"Details: {e}")
            print(traceback.format_exc())
            return None
    
    def _assess_task_complexity(self, prompt):
        """
        Assess if a task needs full planning or simple execution.
        Returns: "low", "medium", or "high"
        """
        prompt_lower = prompt.lower()
        
        # High complexity indicators - needs planning
        high_indicators = [
            "install and configure",
            "setup",
            "deploy",
            "create a project",
            "build and test",
            "analyze and fix",
            "multiple steps",
            "then",
            "after that",
            "debug",
            "troubleshoot"
        ]
        
        # Low complexity - simple command
        low_indicators = [
            "what is",
            "show me",
            "list",
            "display",
            "check if",
            "tell me"
        ]
        
        if any(ind in prompt_lower for ind in high_indicators):
            return "high"
        elif any(ind in prompt_lower for ind in low_indicators):
            return "low"
        else:
            return "medium"
    
    def _query_simple(self, prompt, clear_thinking=False):
        """
        Simple agentic loop for straightforward tasks.
        Same as before - fast execution.
        """
        self.history.append({"role": "user", "content": prompt})

        # Get AI response
        if self.mode == 'digital_ocean':
            response = self._query_digitalocean(prompt, clear_thinking)
        else:
            response = self._query_ollama(prompt, clear_thinking)
        
        if not response:
            return None
        
        # Add AI response to history
        self.history.append({"role": "assistant", "content": response})
        
        # Check if response contains a command
        command, protocol = self._extract_first_command(response)
        
        if command and protocol:
            # Execute the command and return output for feedback loop
            if protocol == "terminal":
                if self.use_agentic_mode:
                    result = self.executor_agent.process(
                        {"command": command, "reason": "User request"},
                        {}
                    )
                else:
                    results = mcp.process_response(
                        f"<mcp:terminal>{command}</mcp:terminal>",
                        require_approval=self.require_approval,
                        auto_approve=self.auto_approve_all
                    )
                    result = results.get("terminal", {})
                
                # Store successful executions
                if result.get("success") and result.get("executed"):
                    knowledge_base.add_command_execution(
                        command=command,
                        output=result.get("output", ""),
                        success=True
                    )
                
                return self._format_execution_feedback(result)
            else:
                # Other protocols
                results = mcp.process_response(
                    f"<mcp:{protocol}>{command}</mcp:{protocol}>",
                    require_approval=self.require_approval,
                    auto_approve=self.auto_approve_all
                )
                result = results.get(protocol, {})
                return self._format_execution_feedback(result)
        
        return None
    
    def _query_with_planning(self, prompt, clear_thinking=False):
        """
        Full agentic mode with visible CoT reasoning and planning.
        Shows reasoning steps, creates plan, executes with feedback.
        """
        print("\n" + "="*60)
        print("🧠 AGENTIC PLANNING MODE ACTIVATED")
        print("="*60)
        
        # Step 1: Chain of Thought Reasoning
        print("\n💭 Chain of Thought Reasoning:")
        cot_prompt = f"""Analyze this task and provide step-by-step reasoning:

Task: {prompt}

Provide your reasoning in this format:
1. Understand: [What is the user asking for?]
2. Requirements: [What do we need to accomplish this?]
3. Approach: [How should we do it?]
4. Steps: [What are the main steps?]
5. Considerations: [Any risks or special considerations?]

Be concise and focused."""
        
        self.history.append({"role": "user", "content": cot_prompt})
        
        if self.mode == 'digital_ocean':
            cot_response = self._query_digitalocean(cot_prompt, clear_thinking=False)
        else:
            cot_response = self._query_ollama(cot_prompt, clear_thinking=False)
        
        if cot_response:
            self.history.append({"role": "assistant", "content": cot_response})
            print("")  # New line after CoT
        
        # Step 2: Create Execution Plan
        print("\n📋 Creating Execution Plan:")
        plan_prompt = f"""Based on the reasoning above, create a step-by-step execution plan.

List ONLY the commands to execute, one per line, in order.
Format each as: <mcp:terminal>command</mcp:terminal>

Do NOT include explanations, just the commands."""
        
        self.history.append({"role": "user", "content": plan_prompt})
        
        if self.mode == 'digital_ocean':
            plan_response = self._query_digitalocean(plan_prompt, clear_thinking=False)
        else:
            plan_response = self._query_ollama(plan_prompt, clear_thinking=False)
        
        if not plan_response:
            print("❌ Failed to create execution plan")
            return None
        
        self.history.append({"role": "assistant", "content": plan_response})
        
        # Extract all commands from plan
        commands = self._extract_commands(plan_response)
        
        if not commands:
            print("No commands found in plan")
            return None
        
        print(f"\n✓ Plan created with {len(commands)} steps")
        
        # Step 3: Execute Plan Step-by-Step
        print("\n⚡ Executing Plan:\n")
        
        execution_results = []
        for i, command in enumerate(commands, 1):
            print(f"Step {i}/{len(commands)}: {command}")
            
            # Execute command
            if self.use_agentic_mode:
                result = self.executor_agent.process(
                    {"command": command, "reason": f"Plan step {i}"},
                    {}
                )
            else:
                results = mcp.process_response(
                    f"<mcp:terminal>{command}</mcp:terminal>",
                    require_approval=self.require_approval,
                    auto_approve=self.auto_approve_all
                )
                result = results.get("terminal", {})
            
            execution_results.append({
                "step": i,
                "command": command,
                "result": result
            })
            
            # Check if user denied
            if not result.get("approved", True):
                print(f"\n❌ Step {i} denied by user. Stopping plan execution.")
                break
            
            # Check if execution failed
            if not result.get("executed"):
                print(f"\n❌ Step {i} failed to execute.")
                break
            
            # Show if there was an error
            if not result.get("success", True):
                print(f"⚠️  Step {i} completed with errors")
            else:
                print(f"✓ Step {i} completed successfully")
            
            # Store successful executions
            if result.get("success") and result.get("executed"):
                knowledge_base.add_command_execution(
                    command=command,
                    output=result.get("output", ""),
                    success=True
                )
        
        # Step 4: Summary
        print("\n" + "="*60)
        success_count = sum(1 for r in execution_results if r["result"].get("success"))
        print(f"📊 Plan Execution Complete: {success_count}/{len(execution_results)} steps successful")
        print("="*60 + "\n")
        
        # Return summary for terminal interface
        return {
            "feedback": f"Plan executed: {success_count}/{len(execution_results)} steps successful",
            "approved": True,
            "executed": True,
            "success": success_count == len(execution_results),
            "plan_results": execution_results
        }
    
    def _format_execution_feedback(self, result):
        """
        Format execution result for feedback to AI.
        """
        if not result.get("approved", True):
            # User denied - return clear message
            return {
                "feedback": "Command execution was denied by user.",
                "approved": False,
                "executed": False
            }
        
        if not result.get("executed"):
            # Execution failed
            error_msg = result.get("error", "Unknown error")
            return {
                "feedback": f"Command execution failed: {error_msg}",
                "approved": True,
                "executed": False,
                "error": error_msg
            }
        
        # Command executed successfully
        output = result.get("output", "").strip()
        
        # Truncate very long output
        if len(output) > 2000:
            output = output[:2000] + "\n... [Output Truncated]"
        
        # Check for errors in output
        has_error = not result.get("success", True)
        
        if has_error:
            feedback = f"Command output (contains errors):\n{output}"
        else:
            feedback = f"Command output:\n{output}"
        
        return {
            "feedback": feedback,
            "approved": True,
            "executed": True,
            "success": result.get("success", True),
            "output": output
        }

    def _process_response_with_monitoring(self, response):
        """
        Process response with monitoring and error detection.
        Returns execution result for agentic loop.
        """
        # Extract commands from response
        commands = self._extract_commands(response)
        
        if not commands:
            return None  # No commands to execute
        
        # Execute all commands and collect results
        all_results = []
        
        for command in commands:
            if self.use_agentic_mode:
                # Use executor agent with retry logic
                result = self.executor_agent.process(
                    {"command": command, "reason": "User request"},
                    {}
                )
            else:
                # Use simple MCP processing
                results = mcp.process_response(
                    f"<mcp:terminal>{command}</mcp:terminal>",
                    require_approval=self.require_approval,
                    auto_approve=self.auto_approve_all
                )
                result = results.get("terminal", {})
            
            all_results.append(result)

            # If user denied this command, stop processing further commands from the same response
            if not result.get("approved", True):
                break
            
            # Store successful executions in knowledge base
            if result.get("success") and result.get("executed"):
                knowledge_base.add_command_execution(
                    command=command,
                    output=result.get("output", ""),
                    success=True
                )
        
        # Compile results for feedback
        return self._compile_execution_results(all_results)
    
    def _extract_commands(self, response):
        """Extract commands from AI response"""
        # Match <mcp:terminal>command</mcp:terminal> tags
        pattern = r'<mcp:terminal>(.*?)</mcp:terminal>'
        commands = re.findall(pattern, response, re.DOTALL)
        return [cmd.strip() for cmd in commands]
    
    def _compile_execution_results(self, results):
        """Compile execution results for feedback to AI"""
        if not results:
            return None
        
        # If only one result, return it directly
        if len(results) == 1:
            result = results[0]
            if result.get("executed"):
                output = result.get("output", "").strip()
                if len(output) > 2000:
                    output = output[:2000] + "\n... [Output Truncated]"
                
                # Check for errors in output
                has_error = not result.get("success", True)
                
                if has_error:
                    return f"Command executed but encountered an error:\n{output}\n\nPlease analyze this error and suggest a solution."
                else:
                    return f"Command executed successfully.\n{output}"
            
            elif not result.get("approved"):
                # Explicitly handle denials as non-errors to avoid agentic escalation
                return "Command execution was denied by user."
            
            elif result.get("error"):
                return f"Command execution failed: {result.get('error')}\n\nPlease try a different approach."
            
            # Multiple results
        output_parts = []
        for i, result in enumerate(results, 1):
            if result.get("executed"):
                output = result.get("output", "")[:500]
                output_parts.append(f"Command {i}: {output}")
        
        return "\n\n".join(output_parts)