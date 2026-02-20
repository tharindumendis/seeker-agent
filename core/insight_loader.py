"""Utility for loading agent insights from markdown and text files."""
from pathlib import Path
from typing import Dict, List


class InsightLoader:
    """Loads and manages agent insights from the Agent_Insight directory."""
    
    def __init__(self, insight_dir: Path):
        """
        Initialize the insight loader.
        
        Args:
            insight_dir: Path to the Agent_Insight directory
        """
        self.insight_dir = Path(insight_dir)
        self.insights: Dict[str, str] = {}
        
    def load_insights(self) -> Dict[str, str]:
        """
        Load all .md and .txt files from the insight directory.
        
        Returns:
            Dictionary mapping filename to content
        """
        if not self.insight_dir.exists():
            print(f"⚠️  Insight directory not found: {self.insight_dir}")
            return {}
        
        insights = {}
        
        # Load markdown files
        for md_file in self.insight_dir.glob("*.md"):
            try:
                content = md_file.read_text(encoding='utf-8')
                insights[md_file.stem] = content
                print(f"✓ Loaded insight: {md_file.name}")
            except Exception as e:
                print(f"⚠️  Failed to load {md_file.name}: {e}")
        
        # Load text files
        for txt_file in self.insight_dir.glob("*.txt"):
            try:
                content = txt_file.read_text(encoding='utf-8')
                insights[txt_file.stem] = content
                print(f"✓ Loaded insight: {txt_file.name}")
            except Exception as e:
                print(f"⚠️  Failed to load {txt_file.name}: {e}")
        
        self.insights = insights
        return insights
    
    def format_for_prompt(self) -> str:
        """
        Format loaded insights for inclusion in the system prompt.
        
        Returns:
            Formatted string containing all insights
        """
        if not self.insights:
            return ""
        
        formatted = "Agent Insights:\n"
        formatted += "=" * 60 + "\n\n"
        
        # Prioritize certain files
        priority_order = ['ultimate_goals', 'simple_goals']
        
        # Add priority insights first
        for key in priority_order:
            if key in self.insights:
                formatted += f"{self.insights[key]}\n\n"
        
        # Add remaining insights
        for key, content in self.insights.items():
            if key not in priority_order:
                formatted += f"{content}\n\n"
        
        formatted += "=" * 60 + "\n"
        return formatted
    
    def get_insight(self, name: str) -> str:
        """
        Get a specific insight by name.
        
        Args:
            name: Name of the insight file (without extension)
            
        Returns:
            Content of the insight, or empty string if not found
        """
        return self.insights.get(name, "")
    
    def list_insights(self) -> List[str]:
        """
        List all loaded insight names.
        
        Returns:
            List of insight names
        """
        return list(self.insights.keys())
    
    def reload(self) -> Dict[str, str]:
        """
        Reload all insights from disk.
        
        Returns:
            Updated insights dictionary
        """
        return self.load_insights()
