"""Memory management for Seeker agent."""
from typing import List, Dict, Any
from datetime import datetime
import json


class MemoryManager:
    """Manages agent memory and history."""
    
    def __init__(self, memory_limit: int = 10, history_limit: int = 50):
        """
        Initialize memory manager.
        
        Args:
            memory_limit: Maximum number of memory entries before summarization
            history_limit: Maximum number of history entries to keep
        """
        self.memory_limit = memory_limit
        self.history_limit = history_limit
        self.memory: List[Dict[str, Any]] = []
        self.history: List[Dict[str, Any]] = []
        self.summaries: List[Dict[str, Any]] = []
    
    def add_memory(self, entry: Dict[str, Any]):
        """Add an entry to memory."""
        entry['timestamp'] = datetime.now().isoformat()
        self.memory.append(entry)
    
    def add_history(self, entry: Dict[str, Any]):
        """Add an entry to history."""
        entry['timestamp'] = datetime.now().isoformat()
        self.history.append(entry)
        
        # Trim history if it exceeds limit
        if len(self.history) > self.history_limit:
            self.history = self.history[-self.history_limit:]
    
    def get_recent_memory(self, count: int = 15) -> List[Dict[str, Any]]:
        """Get the most recent memory entries."""
        return self.memory[-count:] if self.memory else []
    
    def get_recent_history(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent history entries."""
        return self.history[-count:] if self.history else []
    
    def should_summarize(self) -> bool:
        """Check if memory should be summarized."""
        return len(self.memory) > self.memory_limit
    
    def create_summary(self, summary_content: str):
        """Create a summary and clear memory."""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'content': summary_content,
            'entries_summarized': len(self.memory)
        }
        self.summaries.append(summary)
        self.memory.clear()
        self.memory.append({
            'type': 'summary',
            'summary': summary_content,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_tool_execution_history(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent tool executions only."""
        tool_executions = [
            entry for entry in self.memory 
            if entry.get('type') == 'tool_execution'
        ]
        return tool_executions[-count:] if tool_executions else []
    
    def get_context_for_llm(self) -> str:
        """Get formatted context for LLM prompt."""
        context_parts = []
        
        # Add recent summaries
        if self.summaries:
            recent_summaries = self.summaries[-2:]  # Last 2 summaries
            context_parts.append("Previous summaries:")
            for summary in recent_summaries:
                context_parts.append(f"  - {summary['content']}")
        
        # Add tool execution history (CRITICAL for avoiding redundant calls)
        tool_history = self.get_tool_execution_history()
        if tool_history:
            context_parts.append(f"\nTool Execution History ({len(tool_history)} recent calls):")
            for entry in tool_history:
                tool_name = entry.get('tool_name', 'unknown')
                args = entry.get('args', {})
                result = entry.get('result', '')
                # Format args for display
                args_str = ', '.join([f"{k}={v}" for k, v in args.items()]) if args else 'no args'
                context_parts.append(f"  • {tool_name}({args_str}) → {result[:150]}...")
        
        # Add recent memory (all types)
        recent_memory = self.get_recent_memory()
        if recent_memory:
            context_parts.append(f"\nRecent Activity ({len(recent_memory)} entries):")
            for entry in recent_memory:
                entry_type = entry.get('type', 'unknown')
                
                if entry_type == 'summary':
                    context_parts.append(f"  [Summary] {entry.get('summary', '')}")
                
                elif entry_type == 'tool_execution':
                    tool_name = entry.get('tool_name', 'unknown')
                    result = entry.get('result', '')
                    context_parts.append(f"  [Tool: {tool_name}] {result[:100]}...")
                
                elif entry_type == 'llm_response':
                    prompt = entry.get('prompt', '')
                    context_parts.append(f"  [User] {prompt[:100]}...")
                
                elif entry_type == 'user_input':
                    content = entry.get('content', '')
                    context_parts.append(f"  [User] {content[:100]}...")
        
        return "\n".join(context_parts) if context_parts else "No previous context"
    
    def save_to_file(self, filepath: str):
        """Save memory and history to a JSON file."""
        data = {
            'memory': self.memory,
            'history': self.history,
            'summaries': self.summaries,
            'saved_at': datetime.now().isoformat()
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def load_from_file(self, filepath: str):
        """Load memory and history from a JSON file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            self.memory = data.get('memory', [])
            self.history = data.get('history', [])
            self.summaries = data.get('summaries', [])
        except FileNotFoundError:
            print(f"Memory file not found: {filepath}")
        except Exception as e:
            print(f"Error loading memory: {e}")
    
    def clear(self):
        """Clear all memory and history."""
        self.memory.clear()
        self.history.clear()
        self.summaries.clear()
    
    def __repr__(self):
        return (
            f"MemoryManager(memory={len(self.memory)}, "
            f"history={len(self.history)}, "
            f"summaries={len(self.summaries)})"
        )
