import readline

class TerminalInterface:
    def __init__(self, ai_terminal, config):
        self.ai_terminal = ai_terminal
        self.config = config
        self.commands = ['history','exit']

    def completer(self, text, state):
        options = [i for i in self.commands if i.startswith(text)]
        if state < len(options):
            return options[state]
        else:
            return None

    def run(self):
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.completer)
        print("\033[1;34mWelcome to CogniOrch Terminal.\033[0m")
        while True:
            try:
                user_input = input("\033[1;32mYou:\033[0m ").strip()
                if user_input.lower() in ['exit']:
                    print("\033[1;31mGoodbye!\033[0m")
                    break
                elif user_input.lower() == 'history':
                    print("\033[1;33mDisplaying conversation history\033[0m")
                    self.display_history()
                else:
                    # Start agentic loop (auto-detects simple vs planning mode)
                    current_prompt = user_input
                    loop_count = 0
                    max_loops = 5
                    
                    while loop_count < max_loops:
                        # Query AI with current prompt
                        execution_result = self.ai_terminal.query(current_prompt)
                        
                        # If no execution result, AI is done (no command in response)
                        if not execution_result:
                            break
                        
                        # Check if this was a planning mode execution (multi-step)
                        if "plan_results" in execution_result:
                            # Planning mode handled everything, we're done
                            break
                        
                        # Check if user denied the command
                        if not execution_result.get("approved", True):
                            print("\n\033[1;33m[System] Command denied by user. Stopping.\033[0m")
                            break
                        
                        # Check if execution failed
                        if not execution_result.get("executed", False):
                            print("\n\033[1;31m[System] Command execution failed.\033[0m")
                            # Feed the error back to AI
                            error_msg = execution_result.get("error", "Unknown error")
                            current_prompt = f"The command failed with error: {error_msg}\n\nPlease try a different approach or report the issue to the user."
                            loop_count += 1
                            continue
                        
                        # Feed REAL output back to AI for analysis
                        feedback = execution_result.get("feedback", "")
                        current_prompt = feedback
                        
                        loop_count += 1
                    
                    if loop_count >= max_loops:
                        print("\n\033[1;33m[System] Maximum automatic steps reached.\033[0m")
            except KeyboardInterrupt:
                print("\n\033[1;31mInterrupted. Goodbye!\033[0m")
                break
            except Exception as e:
                print(f"\033[1;31mAn error occurred: {str(e)}\033[0m")

    def display_history(self):
        for entry in self.ai_terminal.get_conversation_history():
            role = "\033[1;32mYou:\033[0m" if entry["role"] == "user" else "\033[1;34mCogniOrch:\033[0m"
            print(f"{role} {entry['content']}")