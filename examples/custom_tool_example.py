"""Example of creating a custom tool for Seeker agent."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.base import BaseTool
from typing import List


class CalculatorTool(BaseTool):
    """Example custom tool: Simple calculator."""
    
    name = "calculator"
    description = "Perform basic arithmetic operations (add, subtract, multiply, divide)"
    parameters = {
        "operation": {
            "type": "string",
            "description": "Operation to perform: add, subtract, multiply, divide"
        },
        "a": {
            "type": "number",
            "description": "First number"
        },
        "b": {
            "type": "number",
            "description": "Second number"
        }
    }
    
    def execute(self, operation: str, a: float, b: float) -> str:
        """Execute arithmetic operation."""
        operations = {
            'add': lambda x, y: x + y,
            'subtract': lambda x, y: x - y,
            'multiply': lambda x, y: x * y,
            'divide': lambda x, y: x / y if y != 0 else "Error: Division by zero"
        }
        
        if operation not in operations:
            return f"Error: Unknown operation '{operation}'. Use: add, subtract, multiply, divide"
        
        try:
            result = operations[operation](a, b)
            return f"{a} {operation} {b} = {result}"
        except Exception as e:
            return f"Error: {e}"


class TextAnalyzerTool(BaseTool):
    """Example custom tool: Analyze text."""
    
    name = "text_analyzer"
    description = "Analyze text and return statistics (word count, character count, etc.)"
    parameters = {
        "text": {
            "type": "string",
            "description": "Text to analyze"
        }
    }
    
    def execute(self, text: str) -> dict:
        """Analyze text and return statistics."""
        words = text.split()
        sentences = text.split('.')
        
        return {
            "characters": len(text),
            "characters_no_spaces": len(text.replace(" ", "")),
            "words": len(words),
            "sentences": len([s for s in sentences if s.strip()]),
            "average_word_length": sum(len(word) for word in words) / len(words) if words else 0,
            "unique_words": len(set(words))
        }


class FileCounterTool(BaseTool):
    """Example custom tool: Count files by extension."""
    
    name = "count_files_by_extension"
    description = "Count files in a directory grouped by file extension"
    parameters = {
        "directory": {
            "type": "string",
            "description": "Directory path to analyze"
        }
    }
    
    def execute(self, directory: str) -> dict:
        """Count files by extension."""
        import os
        from collections import defaultdict
        
        try:
            extension_counts = defaultdict(int)
            total_files = 0
            
            for root, _, files in os.walk(directory):
                for file in files:
                    total_files += 1
                    ext = Path(file).suffix or 'no_extension'
                    extension_counts[ext] += 1
            
            return {
                "total_files": total_files,
                "by_extension": dict(extension_counts),
                "unique_extensions": len(extension_counts)
            }
        except Exception as e:
            return {"error": str(e)}


# Example usage
if __name__ == "__main__":
    print("=== Custom Tool Examples ===\n")
    
    # Test Calculator Tool
    calc = CalculatorTool()
    print(f"Calculator Tool: {calc.name}")
    print(f"Description: {calc.description}")
    print(f"Result: {calc.execute('add', 10, 5)}")
    print(f"Result: {calc.execute('multiply', 7, 8)}\n")
    
    # Test Text Analyzer Tool
    analyzer = TextAnalyzerTool()
    print(f"Text Analyzer Tool: {analyzer.name}")
    sample_text = "This is a sample text. It has multiple sentences. Let's analyze it!"
    result = analyzer.execute(sample_text)
    print(f"Analysis: {result}\n")
    
    # Test File Counter Tool
    counter = FileCounterTool()
    print(f"File Counter Tool: {counter.name}")
    result = counter.execute(".")
    print(f"File count: {result}")
    
    # Show tool schema
    print("\n=== Tool Schema (for LLM) ===")
    print(calc.get_schema())
