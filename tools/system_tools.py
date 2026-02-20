"""System tools for Seeker agent."""
import subprocess
import os
from datetime import datetime
from typing import Dict, Any
from .base import BaseTool
from core.tool_queue import tool_queue


class ExecuteCommandTool(BaseTool):
    """Tool for executing system commands."""
    
    name = "execute_command"
    description = "Execute a system command and return output (requires user approval)"
    parameters = {
        "command": {
            "type": "string",
            "description": "Command to execute"
        }
    }
    
    def execute(self, command: str) -> str:
        """
        Execute command with user approval via queue system.
        
        This is NON-BLOCKING - the tool is added to a queue and the agent
        continues working. User approves via web interface, then tool executes.
        """
        try:
            # Add to pending queue (non-blocking)
            tool_id = tool_queue.add_tool(
                tool_name=self.name,
                args={"command": command}
            )
            
            # Return pending status immediately
            return f"⏳ Command queued for approval (ID: {tool_id[:8]}...)\n" \
                   f"Command: {command}\n" \
                   f"Status: Waiting for user approval via web interface"
            
        except Exception as e:
            return f"Error queueing command: {str(e)}"


class GetTimeTool(BaseTool):
    """Tool for getting current time."""
    
    name = "get_time"
    description = "Get the current date and time"
    
    def execute(self) -> str:
        """Return current timestamp."""
        return datetime.now().isoformat()


class WaitForTaskTool(BaseTool):
    """Tool for waiting for new user input."""
    
    name = "wait_for_task"
    description = "Wait for user to provide a new task"
    
    def execute(self) -> str:
        """Wait for user input."""
        return "Waiting for new task..."
