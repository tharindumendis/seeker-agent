# Seeker Agent Framework

A powerful, extensible AI agent framework with plugin-based tool registration system.

## Features

- **Plugin-based Architecture**: Easy tool registration and management
- **Modular Design**: Separate concerns with clean interfaces
- **Memory Management**: Automatic memory summarization
- **Error Handling**: Robust retry logic and error recovery
- **Extensible**: Add new tools as plugins without modifying core code

## Project Structure

```
Seeker/
├── core/
│   ├── __init__.py
│   ├── agent.py          # Main agent class
│   ├── llm_client.py     # LLM interaction layer
│   └── memory.py         # Memory management
├── tools/
│   ├── __init__.py
│   ├── base.py           # Base tool class
│   ├── file_tools.py     # File system operations
│   ├── web_tools.py      # Web-related tools
│   └── system_tools.py   # System utilities
├── plugins/
│   ├── __init__.py
│   └── registry.py       # Tool registration system
├── config/
│   ├── __init__.py
│   └── settings.py       # Configuration management
├── main.py               # Entry point
└── README.md
```

## Usage

```python
from Seeker import SeekerAgent

# Initialize agent
agent = SeekerAgent()

# Run interactively
agent.run_interactive()

# Or process single task
response = agent.process_task("Your task here")
```

## Adding New Tools

Create a new tool by extending the `BaseTool` class:

```python
from tools.base import BaseTool

class MyCustomTool(BaseTool):
    name = "my_custom_tool"
    description = "Description of what this tool does"
    
    def execute(self, **kwargs):
        # Your tool logic here
        return result
```

The tool will be automatically registered and available to the agent.
