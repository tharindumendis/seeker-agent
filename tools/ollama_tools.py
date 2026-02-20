"""Ollama tools for Seeker agent."""
import ollama
from typing import Dict, Any, List, Optional
from .base import BaseTool


class OllamaChatTool(BaseTool):
    """Tool for chatting with Ollama models directly."""
    
    name = "ollama_chat"
    description = "Chat with an Ollama model directly"
    parameters = {
        "model": {
            "type": "string",
            "description": "Name of the Ollama model to use"
        },
        "prompt": {
            "type": "string",
            "description": "Prompt to send to the model"
        },
        "options": {
            "type": "object",
            "description": "Additional options for the model (optional)",
            "properties": {
                "temperature": {
                    "type": "number",
                    "description": "Temperature for generation (default: 0.8)"
                },
                "max_tokens": {
                    "type": "number",
                    "description": "Maximum number of tokens to generate"
                }
            }
        }
    }
    
    def execute(self, model: str, prompt: str, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Chat with an Ollama model.
        
        Args:
            model: Name of the Ollama model to use
            prompt: Prompt to send to the model
            options: Additional options for the model (optional)
            
        Returns:
            Response from the Ollama model
        """
        try:
            # Default options
            opts = {"temperature": 0.8}
            if options:
                opts.update(options)
            
            response = ollama.chat(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                options=opts
            )
            
            return response['message']['content']
        except Exception as e:
            return f"Error chatting with Ollama model: {str(e)}"


class OllamaListModelTool(BaseTool):
    """Tool for listing available Ollama models."""
    
    name = "ollama_list_models"
    description = "List all available Ollama models"
    
    def execute(self) -> str:
        """
        List all available Ollama models.
        
        Returns:
            List of available Ollama models
        """
        try:
            response = ollama.list()
            models = [model['name'] for model in response['models']]
            return f"Available Ollama models: {', '.join(models)}"
        except Exception as e:
            return f"Error listing Ollama models: {str(e)}"


class OllamaPullModelTool(BaseTool):
    """Tool for pulling Ollama models."""
    
    name = "ollama_pull_model"
    description = "Pull/download an Ollama model"
    parameters = {
        "model": {
            "type": "string",
            "description": "Name of the Ollama model to pull"
        }
    }
    
    def execute(self, model: str) -> str:
        """
        Pull/download an Ollama model.
        
        Args:
            model: Name of the Ollama model to pull
            
        Returns:
            Status of the pull operation
        """
        try:
            # This will pull the model if it doesn't exist
            response = ollama.pull(model)
            return f"Successfully pulled model: {model}"
        except Exception as e:
            return f"Error pulling Ollama model: {str(e)}"
