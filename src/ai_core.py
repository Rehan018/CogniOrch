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
        self.mode = config.get('mode', 'lm_studio')
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

        self.lm_studio_config = config.get('lm_studio_config', {})
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
        context_commands = [
            "pwd",
            "ls"
        ]
        context_data = load_persistent_memory()
        initial_context = "<context>\n"

        for command in context_commands:
            result = execute_command(command)
            initial_context += f"Command: {command}\nResult:\n{result}\n"

        system_instructions = """
SYSTEM INSTRUCTIONS - FOLLOW STRICTLY:
You are CogniOrch, an advanced AI terminal assistant with agentic capabilities.

COMMAND EXECUTION:
- Wrap commands in <mcp:terminal>command</mcp:terminal> tags
- For system updates, use the correct package manager (apt/dnf/pacman) based on OS info
- You can execute multiple commands in sequence to solve complex problems

AGENTIC BEHAVIOR:
- When you execute a command, you'll receive the output
- Analyze the output to determine if your goal was achieved
- If there's an error, identify the problem and try a different approach
- Continue until the task is completed or you determine it's impossible
- Show your reasoning process step by step

CRITICAL RULES:
1. After receiving command output, ALWAYS analyze it for errors
2. If you see an error, diagnose it and try to fix it
3. Be proactive - if something fails, try alternative solutions
4. Keep track of what you've tried to avoid loops
5. After successful completion, provide a clear summary

EXAMPLES OF AGENTIC BEHAVIOR:

User: "install htop"
You: <mcp:terminal>sudo apt install htop</mcp:terminal>
[If error: "E: Unable to locate package htop"]
You: I see apt couldn't find htop. Let me update the package list first.
<mcp:terminal>sudo apt update</mcp:terminal>
[After update succeeds]
You: Now let me try installing htop again.
<mcp:terminal>sudo apt install htop -y</mcp:terminal>
[After success]
You: Successfully installed htop. It's now available on your system.

Remember: Be proactive, self-correcting, and persistent.
"""
        full_context = f"{system_instructions}\n\n{context_data}\n\n{initial_context}</context>"
        self.context_initialized = True
        return full_context

    def _query_lm_studio(self, prompt, clear_thinking=False):
        instruction = f"{self.lm_studio_config.get('input_prefix', '### Instruction:')} {prompt} {self.lm_studio_config.get('input_suffix', '### Response:')}"

        messages = self.history.copy()
        messages.append({"role": "user", "content": instruction})

        try:
            completion = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                stream=self.is_streaming_mode,
            )

            full_response = ""
            is_first_chunk = True

            for chunk in completion:
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    content = chunk['choices'][0]['delta'].get('content', '')
                    if content:
                        if is_first_chunk:
                            if clear_thinking:
                                print('\r' + ' ' * 30 + '\r', end="", flush=True)
                            print("\033[1;34mCogniOrch:\033[0m ", end='', flush=True)
                            is_first_chunk = False

                        print(content, end='', flush=True)
                        full_response += content

            print()
            return full_response  # Return raw response, processing happens in query()

        except Exception as e:
            print(f"Error while querying LM Studio: {e}")
            return "An error occurred while querying LM Studio."

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

    def query(self, prompt, clear_thinking=False):
        """
        Main query method with agentic loop.
        """
        try:
            if not self.context_initialized:
                context = self.initialize_context()
                prompt = f"{context}\n\n{prompt}"

            self.history.append({"role": "user", "content": prompt})

            # Get AI response
            if self.mode == 'digital_ocean':
                response = self._query_digitalocean(prompt, clear_thinking)
            else:
                response = self._query_lm_studio(prompt, clear_thinking)
            
            if not response:
                return None
            
            # Add AI response to history
            self.history.append({"role": "assistant", "content": response})
            
            # Process commands in response
            execution_result = self._process_response_with_monitoring(response)
            
            return execution_result
            
        except Exception as e:
            import traceback
            logger.error(f"Query error: {e}")
            print(f"Details: {e}")
            print(traceback.format_exc())
            return None

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