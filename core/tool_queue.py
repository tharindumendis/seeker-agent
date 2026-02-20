"""Pending Tool Queue for async approval workflow."""
import time
import uuid
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class PendingTool:
    """Represents a tool awaiting approval."""
    id: str
    tool_name: str
    args: Dict[str, Any]
    status: str  # pending, approved, denied, completed, error
    timestamp: float
    result: Optional[Any] = None
    error: Optional[str] = None
    user_response: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'tool_name': self.tool_name,
            'args': self.args,
            'status': self.status,
            'timestamp': self.timestamp,
            'result': str(self.result) if self.result else None,
            'error': self.error,
            'user_response': self.user_response,
            'created_at': datetime.fromtimestamp(self.timestamp).isoformat()
        }


class PendingToolQueue:
    """
    Manages pending tool executions that require user approval.
    
    This allows the agent to continue working while tools await approval,
    preventing server blocking.
    """
    
    def __init__(self):
        self.pending_tools: Dict[str, PendingTool] = {}
        self.lock = threading.Lock()
        self.on_new_pending = None  # Callback for WebSocket notifications
    
    def add_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """
        Add a tool to the pending queue.
        
        Args:
            tool_name: Name of the tool
            args: Tool arguments
            
        Returns:
            Unique tool ID
        """
        tool_id = str(uuid.uuid4())
        
        pending_tool = PendingTool(
            id=tool_id,
            tool_name=tool_name,
            args=args,
            status='pending',
            timestamp=time.time()
        )
        
        with self.lock:
            self.pending_tools[tool_id] = pending_tool
        
        print(f"📋 Added to pending queue: {tool_name} (ID: {tool_id[:8]}...)")
        
        # Notify WebSocket clients
        if self.on_new_pending:
            try:
                self.on_new_pending(pending_tool.to_dict())
            except Exception as e:
                print(f"⚠️ Failed to notify WebSocket clients: {e}")
        
        return tool_id
    
    def approve_tool(self, tool_id: str, user_response: Optional[str] = None) -> bool:
        """
        Approve a pending tool for execution.
        
        Args:
            tool_id: ID of the tool to approve
            user_response: Optional user input for the tool
            
        Returns:
            True if approved successfully
        """
        with self.lock:
            if tool_id not in self.pending_tools:
                print(f"⚠️ Tool {tool_id[:8]}... not found in queue")
                return False
            
            tool = self.pending_tools[tool_id]
            if tool.status != 'pending':
                print(f"⚠️ Tool {tool_id[:8]}... already {tool.status}")
                return False
            
            tool.status = 'approved'
            tool.user_response = user_response
            print(f"✅ Approved: {tool.tool_name} (ID: {tool_id[:8]}...)")
            return True
    
    def deny_tool(self, tool_id: str, reason: Optional[str] = None) -> bool:
        """
        Deny a pending tool.
        
        Args:
            tool_id: ID of the tool to deny
            reason: Optional reason for denial
            
        Returns:
            True if denied successfully
        """
        with self.lock:
            if tool_id not in self.pending_tools:
                return False
            
            tool = self.pending_tools[tool_id]
            if tool.status != 'pending':
                return False
            
            tool.status = 'denied'
            tool.error = reason or 'User denied'
            print(f"❌ Denied: {tool.tool_name} (ID: {tool_id[:8]}...)")
            return True
    
    def set_result(self, tool_id: str, result: Any, error: Optional[str] = None):
        """
        Set the result of a tool execution.
        
        Args:
            tool_id: ID of the tool
            result: Execution result
            error: Optional error message
        """
        with self.lock:
            if tool_id not in self.pending_tools:
                return
            
            tool = self.pending_tools[tool_id]
            tool.result = result
            tool.error = error
            tool.status = 'completed' if not error else 'error'
    
    def get_pending(self) -> List[Dict]:
        """
        Get all pending tools.
        
        Returns:
            List of pending tools as dictionaries
        """
        with self.lock:
            return [
                tool.to_dict() 
                for tool in self.pending_tools.values() 
                if tool.status == 'pending'
            ]
    
    def get_tool(self, tool_id: str) -> Optional[PendingTool]:
        """Get a specific tool by ID."""
        with self.lock:
            return self.pending_tools.get(tool_id)
    
    def cleanup_old(self, max_age_seconds: int = 3600):
        """Remove tools older than max_age_seconds."""
        current_time = time.time()
        with self.lock:
            to_remove = [
                tool_id for tool_id, tool in self.pending_tools.items()
                if current_time - tool.timestamp > max_age_seconds
                and tool.status in ['completed', 'denied', 'error']
            ]
            for tool_id in to_remove:
                del self.pending_tools[tool_id]
            
            if to_remove:
                print(f"🧹 Cleaned up {len(to_remove)} old tool(s)")


# Global queue instance
tool_queue = PendingToolQueue()
