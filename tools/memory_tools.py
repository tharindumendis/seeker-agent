"""Memory management tools for the agent."""
from tools.base import BaseTool
from typing import Optional
from pathlib import Path
from datetime import datetime


class SummarizeMemoryTool(BaseTool):
    """Tool for summarizing agent's memory."""
    
    name = "summarize_memory"
    description = "Summarize your current memory and optionally save it to Agent_Insight folder for permanent storage"
    parameters = {
        "save_to_insight": {
            "type": "boolean",
            "description": "If true, saves the summary to Agent_Insight folder for permanent storage"
        },
        "filename": {
            "type": "string",
            "description": "Optional filename for saving to Agent_Insight (e.g., 'project_progress.md'). Only used if save_to_insight is true"
        }
    }
    
    def execute(self, save_to_insight: bool = False, filename: Optional[str] = None) -> str:
        """
        Summarize current memory.
        
        Args:
            save_to_insight: Whether to save summary to Agent_Insight folder
            filename: Optional filename for saving (only used if save_to_insight is True)
            
        Returns:
            Summary of memory and confirmation message
        """
        try:
            # Get the agent instance (passed during tool execution)
            # This is a bit of a hack, but necessary since tools don't have direct access to agent
            import sys
            from pathlib import Path
            
            # Add parent directory to path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            
            # Import here to avoid circular dependency
            from core.memory import MemoryManager
            
            # Note: In actual execution, the agent will pass itself to the tool
            # For now, we'll return instructions on how to use this
            
            result = "Memory summarization requested.\n\n"
            
            if save_to_insight:
                if not filename:
                    filename = f"memory_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                
                result += f"Summary will be saved to: Agent_Insight/{filename}\n"
                result += "\nTo complete this action, the agent's _summarize_memory() method will be called "
                result += "and the result will be saved to the specified file.\n"
            else:
                result += "Summary will be generated but not saved permanently.\n"
                result += "Use save_to_insight=true to save to Agent_Insight folder.\n"
            
            result += "\nMemory summarization helps:\n"
            result += "- Save important discoveries before they're forgotten\n"
            result += "- Reduce context size when prompts get too long\n"
            result += "- Create checkpoints of your progress\n"
            
            return result
            
        except Exception as e:
            return f"Error summarizing memory: {str(e)}"


class ClearMemoryTool(BaseTool):
    """Tool for clearing agent's memory."""
    
    name = "clear_memory"
    description = "Clear your current memory (use with caution! Consider summarizing first)"
    parameters = {}
    
    def execute(self) -> str:
        """
        Clear current memory.
        
        Returns:
            Confirmation message
        """
        return ("Memory clear requested. This will remove all current memory entries.\n"
                "⚠️ WARNING: Consider using 'summarize_memory' with save_to_insight=true "
                "before clearing to preserve important information!")


class SaveInsightTool(BaseTool):
    """Tool for saving important information to Agent_Insight folder."""
    
    name = "save_insight"
    description = "Save important information, tips, or discoveries to Agent_Insight folder for permanent memory"
    parameters = {
        "filename": {
            "type": "string",
            "description": "Name of the file to save (e.g., 'important_discovery.md')"
        },
        "content": {
            "type": "string",
            "description": "The content to save"
        }
    }
    
    def execute(self, filename: str, content: str) -> str:
        """
        Save content to Agent_Insight folder.
        
        Args:
            filename: Name of file to save
            content: Content to write
            
        Returns:
            Confirmation message
        """
        try:
            from pathlib import Path
            
            # Get project root
            project_root = Path(__file__).parent.parent
            insight_dir = project_root / "Agent_Insight"
            
            # Create directory if it doesn't exist
            insight_dir.mkdir(exist_ok=True)
            
            # Ensure filename has .md extension
            if not filename.endswith('.md') and not filename.endswith('.txt'):
                filename += '.md'
            
            # Write file
            filepath = insight_dir / filename
            filepath.write_text(content, encoding='utf-8')
            
            return f"✅ Saved to Agent_Insight/{filename}\n\nThis information is now permanently stored and will be loaded in future sessions!"
            
        except Exception as e:
            return f"❌ Error saving insight: {str(e)}"
