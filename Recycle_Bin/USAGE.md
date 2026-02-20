# Seeker Agent - Usage Guide

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Configure environment:

```bash
cp .env.example .env
# Edit .env with your API key and preferences
```

## Running the Agent

### Interactive Mode

```bash
python main.py
```

This starts an interactive session where you can chat with the agent.

### Programmatic Usage

```python
from core.agent import SeekerAgent
from config.settings import Settings

# Create agent with custom settings
settings = Settings()
agent = SeekerAgent(config=settings)

# Process a single task
result = agent.process_task("List all Python files in the current directory")

# Access results
print(result['response'])
for tool_result in result['tool_results']:
    print(f"Tool: {tool_result['tool']}")
    print(f"Result: {tool_result['result']}")
```

## Available Commands (Interactive Mode)

- `exit` - Quit the agent
- `tools` - List all available tools
- `memory` - Show memory status
- Any other input - Process as a task

## Creating Custom Tools

1. Create a new file in `tools/` directory (e.g., `my_tools.py`)

2. Define your tool class:

```python
from tools.base import BaseTool

class MyCustomTool(BaseTool):
    name = "my_tool"
    description = "What this tool does"
    parameters = {
        "param1": {
            "type": "string",
            "description": "Description of param1"
        }
    }

    def execute(self, param1: str) -> str:
        # Your logic here
        return f"Processed: {param1}"
```

3. The tool will be automatically discovered and registered when the agent starts!

## Tool Categories

### File Tools

- `read_file` - Read file contents
- `write_file` - Write to files
- `list_directory` - List directory contents
- `read_file_range` - Read specific line ranges
- `get_current_directory` - Get current working directory

### Web Tools

- `web_fetch` - Fetch content from URLs
- `web_search` - Search the web (placeholder)

### System Tools

- `execute_command` - Run system commands (with approval)
- `get_time` - Get current timestamp
- `wait_for_task` - Wait for new input

## Memory Management

The agent automatically manages memory:

- Stores recent interactions
- Summarizes when memory limit is reached
- Maintains context across conversations

Save/load sessions:

```python
# Save current session
agent.save_session("my_session.json")

# Load previous session
agent.load_session("my_session.json")
```

## Configuration

Edit `.env` or set environment variables:

```bash
# LLM Settings
SEEKER_MODEL=qwen3-coder:480b-cloud
SEEKER_TEMPERATURE=0.7
SEEKER_MAX_RETRIES=3

# Memory Settings
SEEKER_MEMORY_LIMIT=10
SEEKER_HISTORY_LIMIT=50
```

## Architecture

```
User Input
    ↓
SeekerAgent (main.py)
    ↓
├─→ LLMClient (processes with LLM)
├─→ ToolRegistry (manages tools)
├─→ MemoryManager (tracks context)
    ↓
Tool Execution
    ↓
Response to User
```

## Examples

### Example 1: File Operations

```
You: Read the README.md file
Seeker: [Uses read_file tool]
```

### Example 2: Multi-step Task

```
You: Find all Python files and count the lines in each
Seeker: [Uses list_directory, then read_file_range for each file]
```

### Example 3: Web Research

```
You: Fetch the content from https://example.com
Seeker: [Uses web_fetch tool]
```

## Troubleshooting

### Tool not found

- Ensure your tool class inherits from `BaseTool`
- Check that the tool file is in the `tools/` directory
- Verify the tool has `name` and `description` attributes

### LLM connection errors

- Check your `OLLAMA_API_KEY` in `.env`
- Verify Ollama server is running
- Check network connectivity

### Memory issues

- Adjust `SEEKER_MEMORY_LIMIT` in settings
- Clear memory manually: `agent.memory.clear()`
