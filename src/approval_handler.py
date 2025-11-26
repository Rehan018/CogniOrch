"""
Enhanced approval handler for CogniOrch command execution.
Uses a simple bash-style prompt UI for command approval.
"""

from prompt_toolkit import print_formatted_text, HTML
from prompt_toolkit.shortcuts import clear
from prompt_toolkit.styles import Style
from prompt_toolkit import prompt

# Define approval style
APPROVAL_STYLE = Style.from_dict({
    'prompt': '#5fd7ff bold',      # Bright cyan for CogniOrch prompt
    'command': '#ffffff',          # White for command text
    'arrow': '#d787af bold',       # Pink for the arrow
    'question': '#d7d787',         # Light yellow for question
    'success': '#98fb98',          # Pale Green for success
    'error': '#ff6b6b',            # Soft Red for error
})


class ApprovalHandler:
    """Handle command approval requests with a bash-style prompt UI."""

    def __init__(self, require_approval=True, auto_approve_all=False):
        """Initialize approval handler with settings."""
        self.require_approval = require_approval
        self.auto_approve_all = auto_approve_all

    def request_approval(self, command):
        """
        Request approval for command execution with bash-style prompt UI.

        Args:
            command (str): Command to be approved

        Returns:
            bool: True if approved, False otherwise
            str: Always None as we've removed the 'approve all' option
        """
        if not self.require_approval or self.auto_approve_all:
            return True, None

        import html
        escaped_command = html.escape(command)
        
        # Create a box-like structure for the command
        print_formatted_text(HTML(f"\n<ansigray>╭──────────────────────────────────────────────────────────────────╮</ansigray>"), style=APPROVAL_STYLE)
        print_formatted_text(HTML(f"<ansigray>│</ansigray> <prompt>COMMAND APPROVAL REQUIRED</prompt>"), style=APPROVAL_STYLE)
        print_formatted_text(HTML(f"<ansigray>│</ansigray>"), style=APPROVAL_STYLE)
        print_formatted_text(HTML(f"<ansigray>│</ansigray> <command>{escaped_command}</command>"), style=APPROVAL_STYLE)
        print_formatted_text(HTML(f"<ansigray>│</ansigray>"), style=APPROVAL_STYLE)
        print_formatted_text(HTML(f"<ansigray>╰──────────────────────────────────────────────────────────────────╯</ansigray>"), style=APPROVAL_STYLE)

        # Get user input using standard input for better stability
        try:
            # We use print instead of prompt_toolkit for the input line to ensure it works
            print("  ↳ Execute this command? (Allow/Reject) [Y/n]: ", end="", flush=True)
            user_input = input().strip().lower()
        except EOFError:
            user_input = 'n'

        # Handle approval/rejection
        if user_input == 'n' or user_input == 'no':
            print_formatted_text(HTML("  <error>✗</error>"), style=APPROVAL_STYLE)
            return False, None
        else:
            print_formatted_text(HTML("  <success>✓</success>"), style=APPROVAL_STYLE)
            return True, None