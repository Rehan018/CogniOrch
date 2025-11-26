"""
File operation tools for the tool registry.
"""

import os
import glob
import shutil
from typing import List, Optional
from .tool_registry import registry, ToolCategory, ToolParameter


def read_file(path: str, lines: Optional[int] = None) -> str:
    """
    Read contents of a file.
    
    Args:
        path: File path to read
        lines: Optional number of lines to read (from start)
        
    Returns:
        File contents
    """
    try:
        with open(path, 'r') as f:
            if lines:
                content = ''.join(f.readlines()[:lines])
            else:
                content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"


def write_file(path: str, content: str, append: bool = False) -> str:
    """
    Write content to a file.
    
    Args:
        path: File path
        content: Content to write
        append: Whether to append (True) or overwrite (False)
        
    Returns:
        Success message
    """
    try:
        mode = 'a' if append else 'w'
        with open(path, mode) as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


def list_directory(path: str = ".", pattern: Optional[str] = None) -> str:
    """
    List contents of a directory.
    
    Args:
        path: Directory path
        pattern: Optional glob pattern to filter
        
    Returns:
        Directory listing
    """
    try:
        if pattern:
            files = glob.glob(os.path.join(path, pattern))
        else:
            files = os.listdir(path)
        
        return "\n".join(sorted(files))
    except Exception as e:
        return f"Error listing directory: {str(e)}"


def search_files(directory: str, pattern: str, recursive: bool = True) -> str:
    """
    Search for files matching a pattern.
    
    Args:
        directory: Directory to search in
        pattern: Glob pattern
        recursive: Whether to search recursively
        
    Returns:
        List of matching files
    """
    try:
        if recursive:
            pattern_path = os.path.join(directory, "**", pattern)
            files = glob.glob(pattern_path, recursive=True)
        else:
            pattern_path = os.path.join(directory, pattern)
            files = glob.glob(pattern_path)
        
        return "\n".join(sorted(files))
    except Exception as e:
        return f"Error searching files: {str(e)}"


def file_info(path: str) -> str:
    """
    Get information about a file.
    
    Args:
        path: File path
        
    Returns:
        File information
    """
    try:
        stats = os.stat(path)
        info = [
            f"Path: {path}",
            f"Size: {stats.st_size} bytes",
            f"Modified: {stats.st_mtime}",
            f"Permissions: {oct(stats.st_mode)}"
        ]
        return "\n".join(info)
    except Exception as e:
        return f"Error getting file info: {str(e)}"


def create_directory(path: str, parents: bool = True) -> str:
    """
    Create a directory.
    
    Args:
        path: Directory path
        parents: Create parent directories if needed
        
    Returns:
        Success message
    """
    try:
        os.makedirs(path, exist_ok=parents)
        return f"Created directory: {path}"
    except Exception as e:
        return f"Error creating directory: {str(e)}"


# Register all file tools
def register_file_tools():
    """Register all file operation tools"""
    
    registry.register_function(
        name="read_file",
        func=read_file,
        description="Read contents of a file",
        category=ToolCategory.FILE_OPERATIONS,
        parameters=[
            ToolParameter("path", "str", "Path to the file", required=True),
            ToolParameter("lines", "int", "Number of lines to read (optional)", required=False)
        ],
        examples=["read_file('/etc/hosts')", "read_file('log.txt', lines=10)"]
    )
    
    registry.register_function(
        name="write_file",
        func=write_file,
        description="Write content to a file",
        category=ToolCategory.FILE_OPERATIONS,
        parameters=[
            ToolParameter("path", "str", "Path to the file", required=True),
            ToolParameter("content", "str", "Content to write", required=True),
            ToolParameter("append", "bool", "Append mode", required=False, default=False)
        ],
        examples=["write_file('output.txt', 'Hello World')"]
    )
    
    registry.register_function(
        name="list_directory",
        func=list_directory,
        description="List contents of a directory",
        category=ToolCategory.FILE_OPERATIONS,
        examples=["list_directory('.')", "list_directory('/tmp', pattern='*.log')"]
    )
    
    registry.register_function(
        name="search_files",
        func=search_files,
        description="Search for files matching a pattern",
        category=ToolCategory.FILE_OPERATIONS,
        examples=["search_files('.', '*.py')", "search_files('/var/log', '*.log', recursive=True)"]
    )
    
    registry.register_function(
        name="file_info",
        func=file_info,
        description="Get information about a file",
        category=ToolCategory.FILE_OPERATIONS,
        examples=["file_info('/etc/passwd')"]
    )
    
    registry.register_function(
        name="create_directory",
        func=create_directory,
        description="Create a directory",
        category=ToolCategory.FILE_OPERATIONS,
        examples=["create_directory('/tmp/mydir')"]
    )


# Auto-register when module is imported
register_file_tools()
