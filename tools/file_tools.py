"""File system tools for Seeker agent."""
import os
from typing import List
from pathlib import Path
from .base import BaseTool


class ReadFileTool(BaseTool):
    """Tool for reading file contents."""
    
    name = "read_file"
    description = "Read the content of a file with proper encoding handling"
    parameters = {
        "file_path": {
            "type": "string",
            "description": "Absolute or relative path to the file to read"
        }
    }
    
    def execute(self, file_path: str) -> str:
        """Read file with multiple encoding fallbacks."""
        try:
            # Try UTF-8 first
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                # Try with error replacement
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    return f.read()
            except UnicodeDecodeError:
                try:
                    # Fallback to latin-1
                    with open(file_path, 'r', encoding='latin-1') as f:
                        return f.read()
                except Exception as e:
                    return f"Error reading file {file_path}: {e}"
        except Exception as e:
            return f"Error reading file {file_path}: {e}"


class WriteFileTool(BaseTool):
    """Tool for writing content to files."""
    
    name = "write_file"
    description = "Write content to a file, creating directories if needed"
    parameters = {
        "file_path": {
            "type": "string",
            "description": "Path where the file should be written"
        },
        "content": {
            "type": "string",
            "description": "Content to write to the file"
        }
    }
    
    def execute(self, file_path: str, content: str) -> str:
        """Write content to file with directory creation."""
        try:
            # Ensure parent directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Write with UTF-8
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return f"Successfully wrote to {file_path}"
        except UnicodeEncodeError:
            try:
                # Fallback with error handling
                with open(file_path, 'w', encoding='utf-8', errors='ignore') as f:
                    f.write(content)
                return f"Successfully wrote to {file_path} (some characters ignored)"
            except Exception as e:
                return f"Error writing to {file_path}: {e}"
        except Exception as e:
            return f"Error writing to {file_path}: {e}"


class ListDirectoryTool(BaseTool):
    """Tool for listing directory contents."""
    
    name = "list_directory"
    description = "List all files in a directory and its subdirectories"
    parameters = {
        "directory": {
            "type": "string",
            "description": "Directory path to list"
        }
    }
    
    def execute(self, directory: str) -> List[str]:
        """Recursively list all files in directory."""
        try:
            file_list = []
            for root, _, files in os.walk(directory):
                for file in files:
                    file_list.append(os.path.join(root, file))
            return file_list
        except Exception as e:
            return [f"Error listing directory {directory}: {e}"]


class ReadFileRangeTool(BaseTool):
    """Tool for reading specific line ranges from files."""
    
    name = "read_file_range"
    description = "Read specific line range from a file (1-indexed, inclusive)"
    parameters = {
        "file_path": {
            "type": "string",
            "description": "Path to the file"
        },
        "start_line": {
            "type": "integer",
            "description": "Starting line number (1-indexed)"
        },
        "end_line": {
            "type": "integer",
            "description": "Ending line number (1-indexed, inclusive)"
        }
    }
    
    def execute(self, file_path: str, start_line: int, end_line: int) -> str:
        """Read specific line range from file."""
        try:
            if start_line < 1 or end_line < start_line:
                return f"Invalid line range: start={start_line}, end={end_line}"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            if start_line > total_lines:
                return ""
            
            end_line = min(end_line, total_lines)
            selected = lines[start_line - 1:end_line]
            return "".join(selected)
        except Exception as e:
            return f"Error reading file range {file_path}: {e}"


class GetCurrentDirectoryTool(BaseTool):
    """Tool for getting current working directory."""
    
    name = "get_current_directory"
    description = "Get the current working directory path"
    
    def execute(self) -> str:
        """Return current working directory."""
        try:
            return os.getcwd()
        except Exception as e:
            return f"Error getting current directory: {e}"
