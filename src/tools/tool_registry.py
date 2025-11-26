"""
Tool Registry for structured tool/function calling.
Manages registration, validation, and execution of tools.
"""

from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass
from enum import Enum
import logging
import inspect

logger = logging.getLogger("cogniorch.tools")


class ToolCategory(Enum):
    """Categories of tools"""
    FILE_OPERATIONS = "file_operations"
    SYSTEM_INFO = "system_info"
    PROCESS_MANAGEMENT = "process_management"
    NETWORK = "network"
    PACKAGE_MANAGEMENT = "package_management"
    DEVELOPMENT = "development"
    DATABASE = "database"
    UTILITY = "utility"


@dataclass
class ToolParameter:
    """Represents a tool parameter"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None


@dataclass
class Tool:
    """Represents a callable tool"""
    name: str
    description: str
    category: ToolCategory
    parameters: List[ToolParameter]
    function: Callable
    examples: List[str] = None
    
    def __post_init__(self):
        if self.examples is None:
            self.examples = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary format (for LLM)"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default
                }
                for p in self.parameters
            ],
            "examples": self.examples
        }


class ToolRegistry:
    """
    Central registry for all available tools.
    Manages tool registration, discovery, and execution.
    """
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.categories: Dict[ToolCategory, List[str]] = {cat: [] for cat in ToolCategory}
        logger.info("ToolRegistry initialized")
    
    def register(self, tool: Tool):
        """
        Register a new tool.
        
        Args:
            tool: Tool to register
        """
        if tool.name in self.tools:
            logger.warning(f"Tool '{tool.name}' already registered, overwriting")
        
        self.tools[tool.name] = tool
        self.categories[tool.category].append(tool.name)
        logger.info(f"Registered tool: {tool.name} ({tool.category.value})")
    
    def register_function(self,
                         name: str,
                         func: Callable,
                         description: str,
                         category: ToolCategory,
                         parameters: List[ToolParameter] = None,
                         examples: List[str] = None):
        """
        Register a function as a tool.
        
        Args:
            name: Tool name
            func: Function to register
            description: Tool description
            category: Tool category
            parameters: Parameter specifications
            examples: Usage examples
        """
        if parameters is None:
            # Auto-detect parameters from function signature
            parameters = self._infer_parameters(func)
        
        tool = Tool(
            name=name,
            description=description,
            category=category,
            parameters=parameters,
            function=func,
            examples=examples or []
        )
        
        self.register(tool)
    
    def _infer_parameters(self, func: Callable) -> List[ToolParameter]:
        """Infer parameters from function signature"""
        sig = inspect.signature(func)
        parameters = []
        
        for param_name, param in sig.parameters.items():
            if param_name in ['self', 'cls']:
                continue
            
            param_type = str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any"
            required = param.default == inspect.Parameter.empty
            default = None if required else param.default
            
            parameters.append(ToolParameter(
                name=param_name,
                type=param_type,
                description=f"Parameter {param_name}",
                required=required,
                default=default
            ))
        
        return parameters
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self.tools.get(name)
    
    def list_tools(self, category: Optional[ToolCategory] = None) -> List[str]:
        """
        List available tools.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of tool names
        """
        if category:
            return self.categories.get(category, [])
        return list(self.tools.keys())
    
    def execute(self, name: str, **kwargs) -> Any:
        """
        Execute a tool by name.
        
        Args:
            name: Tool name
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result
        """
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")
        
        # Validate parameters
        self._validate_parameters(tool, kwargs)
        
        try:
            logger.debug(f"Executing tool: {name} with params: {kwargs}")
            result = tool.function(**kwargs)
            logger.debug(f"Tool {name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool {name} failed: {str(e)}")
            raise
    
    def _validate_parameters(self, tool: Tool, params: Dict[str, Any]):
        """Validate parameters against tool specification"""
        # Check required parameters
        for param in tool.parameters:
            if param.required and param.name not in params:
                raise ValueError(f"Missing required parameter: {param.name}")
        
        # Check for unknown parameters
        valid_params = {p.name for p in tool.parameters}
        for param_name in params:
            if param_name not in valid_params:
                logger.warning(f"Unknown parameter '{param_name}' for tool '{tool.name}'")
    
    def get_tools_schema(self, category: Optional[ToolCategory] = None) -> List[Dict[str, Any]]:
        """
        Get tools in schema format (for LLM function calling).
        
        Args:
            category: Optional category filter
            
        Returns:
            List of tool schemas
        """
        tool_names = self.list_tools(category)
        return [self.tools[name].to_dict() for name in tool_names]


# Global registry instance
registry = ToolRegistry()
