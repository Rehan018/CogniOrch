import re

class CommandVerifier:
    """
    Verifies terminal commands for safety and correctness.
    """
    
    DANGEROUS_PATTERNS = [
        r"rm\s+-rf\s+/",           # Root deletion
        r"rm\s+-rf\s+/\*",         # Root wildcard deletion
        r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;", # Fork bomb
        r"mkfs",                   # Formatting filesystems
        r"dd\s+if=",               # Direct disk writing
        r">\s*/dev/sd",            # Overwriting devices
        r"chmod\s+777\s+/",        # Global permission opening
        r"mv\s+/\w+\s+/dev/null"   # Moving system dirs to null
    ]

    @staticmethod
    def verify(command: str) -> tuple[bool, str]:
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
