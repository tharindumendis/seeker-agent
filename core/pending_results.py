"""Manager for pending tool results from async execution."""
from typing import Dict, List, Any
from threading import Lock
import time


class PendingToolResult:
    """Represents a tool result waiting to be added to agent context."""
    
    def __init__(self, tool_id: str, tool_name: str, args: dict, result: str):
        self.tool_id = tool_id
        self.tool_name = tool_name
        self.args = args
        self.result = result
        self.timestamp = time.time()
        self.added = False  # Track if added to prompt
    
    def to_dict(self) -> dict:
        return {
            'tool_id': self.tool_id,
            'tool_name': self.tool_name,
            'args': self.args,
            'result': self.result,
            'timestamp': self.timestamp,
            'added': self.added
        }


class PendingToolResultsManager:
    """Manages tool results from async execution that need to be added to agent context."""
    
    def __init__(self):
        self.results: Dict[str, PendingToolResult] = {}
        self.lock = Lock()
    
    def add_result(self, tool_id: str, tool_name: str, args: dict, result: str):
        """Add a new tool result that needs to be communicated to the agent."""
        with self.lock:
            pending_result = PendingToolResult(tool_id, tool_name, args, result)
            self.results[tool_id] = pending_result
            print(f"📋 Added pending tool result: {tool_name} (ID: {tool_id[:8]}...)")
    
    def get_unadded_results(self) -> List[PendingToolResult]:
        """Get all results that haven't been added to a prompt yet."""
        with self.lock:
            return [r for r in self.results.values() if not r.added]
    
    def mark_as_added(self, tool_id: str):
        """Mark a result as added to the agent's context."""
        with self.lock:
            if tool_id in self.results:
                self.results[tool_id].added = True
                print(f"✅ Marked tool result as added: {tool_id[:8]}...")
    
    def mark_all_as_added(self, tool_ids: List[str]):
        """Mark multiple results as added."""
        with self.lock:
            for tool_id in tool_ids:
                if tool_id in self.results:
                    self.results[tool_id].added = True
    
    def cleanup_old_results(self, max_age_seconds: int = 3600):
        """Remove results older than max_age_seconds that have been added."""
        with self.lock:
            current_time = time.time()
            to_remove = []
            
            for tool_id, result in self.results.items():
                if result.added and (current_time - result.timestamp) > max_age_seconds:
                    to_remove.append(tool_id)
            
            for tool_id in to_remove:
                del self.results[tool_id]
            
            if to_remove:
                print(f"🧹 Cleaned up {len(to_remove)} old tool results")
    
    def get_all_results(self) -> List[PendingToolResult]:
        """Get all pending results (for debugging)."""
        with self.lock:
            return list(self.results.values())


# Global instance
pending_tool_results = PendingToolResultsManager()
