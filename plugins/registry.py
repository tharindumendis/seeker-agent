"""Tool registry for automatic tool discovery and registration."""
from typing import Dict, List, Type, Any
import inspect
import importlib
import pkgutil
from pathlib import Path


class ToolRegistry:
    """
    Central registry for all tools in the Seeker framework.
    
    Automatically discovers and registers tools that inherit from BaseTool.
    """
    
    def __init__(self):
        self._tools: Dict[str, Any] = {}
        self._tool_classes: Dict[str, Type] = {}
    
    def register_tool(self, tool_instance):
        """
        Register a tool instance.
        
        Args:
            tool_instance: Instance of a tool class
        """
        if not hasattr(tool_instance, 'name'):
            raise ValueError(f"Tool {tool_instance} must have a 'name' attribute")
        
        tool_name = tool_instance.name
        if tool_name in self._tools:
            print(f"Warning: Tool '{tool_name}' already registered. Overwriting.")
        
        self._tools[tool_name] = tool_instance
        self._tool_classes[tool_name] = tool_instance.__class__
        
    def unregister_tool(self, tool_name: str):
        """Remove a tool from the registry."""
        if tool_name in self._tools:
            del self._tools[tool_name]
            del self._tool_classes[tool_name]
    
    def get_tool(self, tool_name: str):
        """Get a tool instance by name."""
        return self._tools.get(tool_name)
    
    def get_all_tools(self) -> Dict[str, Any]:
        """Get all registered tools."""
        return self._tools.copy()
    
    def get_tool_names(self) -> List[str]:
        """Get list of all registered tool names."""
        return list(self._tools.keys())
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas for all tools (for LLM function calling)."""
        schemas = []
        for tool in self._tools.values():
            if hasattr(tool, 'get_schema'):
                schemas.append(tool.get_schema())
        return schemas
    
    def auto_discover_tools(self, tools_package_path: str = None):
        """
        Automatically discover and register all tools in the tools package.
        
        Args:
            tools_package_path: Path to the tools package (optional)
        """
        if tools_package_path is None:
            # Default to tools package in the same parent directory
            current_file = Path(__file__)
            tools_package_path = current_file.parent.parent / "tools"
        
        # Import the tools package
        try:
            import tools
            from tools.base import BaseTool
            
            # Iterate through all modules in the tools package
            for importer, modname, ispkg in pkgutil.iter_modules(tools.__path__):
                if modname == 'base' or modname.startswith('_'):
                    continue
                
                # Import the module
                module = importlib.import_module(f'tools.{modname}')
                
                # Find all classes that inherit from BaseTool
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, BaseTool) and 
                        obj is not BaseTool and 
                        hasattr(obj, 'name') and 
                        obj.name):
                        try:
                            # Instantiate and register the tool
                            tool_instance = obj()
                            self.register_tool(tool_instance)
                            print(f"✓ Registered tool: {tool_instance.name}")
                        except Exception as e:
                            print(f"✗ Failed to register {name}: {e}")
        
        except ImportError as e:
            print(f"Warning: Could not import tools package: {e}")
        
        # ── MCP server tools ────────────────────────────────────────────────
        try:
            from tools.mcp_tools import discover_mcp_tools
            print("\n🔌 Discovering MCP server tools...")
            mcp_tools = discover_mcp_tools()
            for tool in mcp_tools:
                self.register_tool(tool)
            if mcp_tools:
                print(f"✓ Registered {len(mcp_tools)} MCP tool(s)\n")
            else:
                print("   (no MCP servers configured or all disabled)\n")
        except Exception as e:
            print(f"⚠️  MCP discovery failed: {e}\n")
    
    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Execute a tool by name with given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Parameters to pass to the tool
            
        Returns:
            Tool execution result
        """
        tool = self.get_tool(tool_name)
        if tool is None:
            return f"Error: Tool '{tool_name}' not found"
        
        try:
            return tool.execute(**kwargs)
        except Exception as e:
            return f"Error executing tool '{tool_name}': {e}"
    
    def __repr__(self):
        return f"ToolRegistry(tools={len(self._tools)})"
    
    def __str__(self):
        tools_list = "\n".join([f"  - {name}" for name in self.get_tool_names()])
        return f"ToolRegistry with {len(self._tools)} tools:\n{tools_list}"


# Global registry instance
_global_registry = None


def get_global_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry
