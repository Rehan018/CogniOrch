import re
import os
from typing import Tuple

class CommandVerifier:
    """
    Verifies and classifies commands for safety.
    Identifies potentially dangerous commands and provides warnings.
    """

    # Patterns for dangerous commands
    DANGEROUS_PATTERNS = [
        r'rm\s+-rf\s+/',
        r'mkfs',
        r'dd\s+if=',
        r':\(\)\{\s*:\|:\&\s*\};:',  # Fork bomb
        r'\>\s*/dev/sd[a-z]',
        r'chmod\s+-R\s+777\s+/',
    ]

    @staticmethod
    def verify(command: str) -> Tuple[bool, str]:
        """
        Verify if a command is safe to execute.
        
        Args:
            command: The command to verify
            
        Returns:
            tuple: (is_safe, reason)
        """
        # Check for empty command
        if not command or not command.strip():
            return False, "Command is empty"
            
        # Check for dangerous patterns
        for pattern in CommandVerifier.DANGEROUS_PATTERNS:
            if re.search(pattern, command):
                return False, f"Detected potentially dangerous pattern: {pattern}"
                
        # Heuristic checks
        if "sudo" in command and "rm" in command:
             return True, "Warning: Command uses sudo with rm. Proceed with caution."

        return True, "Command appears safe"
