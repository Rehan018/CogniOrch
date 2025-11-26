"""
System information and operation tools.
"""

import os
import platform
import psutil
import subprocess
from typing import Optional
from .tool_registry import registry, ToolCategory, ToolParameter


def get_system_info() -> str:
    """
    Get comprehensive system information.
    
    Returns:
        System information string
    """
    try:
        info = [
            f"OS: {platform.system()} {platform.release()}",
            f"Distribution: {platform.platform()}",
            f"Architecture: {platform.machine()}",
            f"Processor: {platform.processor()}",
            f"Python: {platform.python_version()}",
            f"Hostname: {platform.node()}"
        ]
        return "\n".join(info)
    except Exception as e:
        return f"Error getting system info: {str(e)}"


def get_disk_usage(path: str = "/") -> str:
    """
    Get disk usage for a path.
    
    Args:
        path: Path to check (default: /)
        
    Returns:
        Disk usage information
    """
    try:
        usage = psutil.disk_usage(path)
        info = [
            f"Path: {path}",
            f"Total: {usage.total / (1024**3):.2f} GB",
            f"Used: {usage.used / (1024**3):.2f} GB",
            f"Free: {usage.free / (1024**3):.2f} GB",
            f"Percent: {usage.percent}%"
        ]
        return "\n".join(info)
    except Exception as e:
        return f"Error getting disk usage: {str(e)}"


def get_memory_info() -> str:
    """
    Get memory usage information.
    
    Returns:
        Memory information
    """
    try:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        info = [
            "=== RAM ===",
            f"Total: {mem.total / (1024**3):.2f} GB",
            f"Available: {mem.available / (1024**3):.2f} GB",
            f"Used: {mem.used / (1024**3):.2f} GB",
            f"Percent: {mem.percent}%",
            "",
            "=== SWAP ===",
            f"Total: {swap.total / (1024**3):.2f} GB",
            f"Used: {swap.used / (1024**3):.2f} GB",
            f"Percent: {swap.percent}%"
        ]
        return "\n".join(info)
    except Exception as e:
        return f"Error getting memory info: {str(e)}"


def get_cpu_info() -> str:
    """
    Get CPU information and usage.
    
    Returns:
        CPU information
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        
        info = [
            f"CPU Count (Physical): {psutil.cpu_count(logical=False)}",
            f"CPU Count (Logical): {psutil.cpu_count(logical=True)}",
            f"CPU Frequency: {psutil.cpu_freq().current:.2f} MHz",
            f"Overall Usage: {psutil.cpu_percent(interval=1)}%",
            "\nPer-Core Usage:"
        ]
        
        for i, percent in enumerate(cpu_percent):
            info.append(f"  Core {i}: {percent}%")
        
        return "\n".join(info)
    except Exception as e:
        return f"Error getting CPU info: {str(e)}"


def list_processes(limit: int = 10) -> str:
    """
    List running processes.
    
    Args:
        limit: Number of processes to show
        
    Returns:
        Process listing
    """
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by CPU usage
        processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
        
        info = ["PID\tNAME\t\tCPU%\tMEM%"]
        info.append("-" * 50)
        
        for proc in processes[:limit]:
            info.append(
                f"{proc['pid']}\t{proc['name'][:15]}\t"
                f"{proc['cpu_percent']:.1f}\t{proc['memory_percent']:.1f}"
            )
        
        return "\n".join(info)
    except Exception as e:
        return f"Error listing processes: {str(e)}"


def get_network_info() -> str:
    """
    Get network interface information.
    
    Returns:
        Network information
    """
    try:
        info = ["=== Network Interfaces ==="]
        
        for interface, addrs in psutil.net_if_addrs().items():
            info.append(f"\n{interface}:")
            for addr in addrs:
                if addr.family == 2:  # AF_INET (IPv4)
                    info.append(f"  IPv4: {addr.address}")
                elif addr.family == 10:  # AF_INET6 (IPv6)
                    info.append(f"  IPv6: {addr.address}")
        
        return "\n".join(info)
    except Exception as e:
        return f"Error getting network info: {str(e)}"


def check_command_exists(command: str) -> str:
    """
    Check if a command exists in PATH.
    
    Args:
        command: Command name to check
        
    Returns:
        Result message
    """
    try:
        result = subprocess.run(
            ["which", command],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return f"Command '{command}' found at: {result.stdout.strip()}"
        else:
            return f"Command '{command}' not found in PATH"
    except Exception as e:
        return f"Error checking command: {str(e)}"


# Register all system tools
def register_system_tools():
    """Register all system operation tools"""
    
    registry.register_function(
        name="get_system_info",
        func=get_system_info,
        description="Get comprehensive system information",
        category=ToolCategory.SYSTEM_INFO,
        examples=["get_system_info()"]
    )
    
    registry.register_function(
        name="get_disk_usage",
        func=get_disk_usage,
        description="Get disk usage information",
        category=ToolCategory.SYSTEM_INFO,
        examples=["get_disk_usage('/')"]
    )
    
    registry.register_function(
        name="get_memory_info",
        func=get_memory_info,
        description="Get memory usage information",
        category=ToolCategory.SYSTEM_INFO,
        examples=["get_memory_info()"]
    )
    
    registry.register_function(
        name="get_cpu_info",
        func=get_cpu_info,
        description="Get CPU information and usage",
        category=ToolCategory.SYSTEM_INFO,
        examples=["get_cpu_info()"]
    )
    
    registry.register_function(
        name="list_processes",
        func=list_processes,
        description="List running processes",
        category=ToolCategory.PROCESS_MANAGEMENT,
        examples=["list_processes(10)"]
    )
    
    registry.register_function(
        name="get_network_info",
        func=get_network_info,
        description="Get network interface information",
        category=ToolCategory.NETWORK,
        examples=["get_network_info()"]
    )
    
    registry.register_function(
        name="check_command_exists",
        func=check_command_exists,
        description="Check if a command exists in PATH",
        category=ToolCategory.UTILITY,
        examples=["check_command_exists('python3')"]
    )


# Auto-register
register_system_tools()
