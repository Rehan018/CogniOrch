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
                    # Initial query
                    response = self.ai_terminal.query(user_input)

                    # If user denied approval, avoid agentic retries to prevent escalation attempts
                    if isinstance(response, str) and 'denied' in response.lower():
                        response = None
                    
                    # Agentic Loop: If response is not None, it means a command was executed and we have output
                    loop_count = 0
                    max_loops = 5
                    
                    while response and loop_count < max_loops:
                        # Feed the output back to the AI
                        # print(f"\n\033[1;30m[Debug] Feeding output back to AI (Loop {loop_count+1})\033[0m")
                        
                        # We treat the command output as a system/user message to the AI
                        response = self.ai_terminal.query(f"System Output:\n{response}")
                        loop_count += 1
                        
                    if loop_count >= max_loops:
                        print("\n\033[1;33m[System] Max automatic steps reached.\033[0m")
            except KeyboardInterrupt:
                print("\n\033[1;31mInterrupted. Goodbye!\033[0m")
                break
            except Exception as e:
                print(f"\033[1;31mAn error occurred: {str(e)}\033[0m")

    def display_history(self):
        for entry in self.ai_terminal.get_conversation_history():
            role = "\033[1;32mYou:\033[0m" if entry["role"] == "user" else "\033[1;34mCogniOrch:\033[0m"
            print(f"{role} {entry['content']}")