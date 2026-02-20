"""Base tool class for all Seeker tools."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import inspect


class BaseTool(ABC):
    """
    Base class for all tools in the Seeker framework.
    
    All tools must inherit from this class and implement the execute method.
    Tools are automatically registered when imported.
    """
    
    # Tool metadata (must be overridden in subclasses)
    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {}
    
    def __init__(self):
        """Initialize the tool."""
        if not self.name:
            raise ValueError(f"{self.__class__.__name__} must define a 'name' attribute")
        if not self.description:
            raise ValueError(f"{self.__class__.__name__} must define a 'description' attribute")
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Tool execution result
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get the tool schema for LLM function calling.
        
        Returns:
            Tool schema in OpenAI function calling format
        """
        # Get execute method signature
        sig = inspect.signature(self.execute)
        parameters = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self' or param_name == 'kwargs':
                continue
            
            param_info = {
                "type": self._get_type_string(param.annotation),
                "description": f"Parameter {param_name}"
            }
            
            # Check if parameter has default value
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
            
            parameters[param_name] = param_info
        
        # Merge with explicitly defined parameters
        if self.parameters:
            parameters.update(self.parameters)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": parameters,
                    "required": required
                }
            }
        }
    
    def _get_type_string(self, annotation) -> str:
        """Convert Python type annotation to JSON schema type."""
        if annotation == inspect.Parameter.empty:
            return "string"
        
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object"
        }
        
        # Handle typing module types
        if hasattr(annotation, '__origin__'):
            origin = annotation.__origin__
            return type_map.get(origin, "string")
        
        return type_map.get(annotation, "string")
    
    def __call__(self, **kwargs) -> Any:
        """Allow tool to be called directly."""
        return self.execute(**kwargs)
    
    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}')"
