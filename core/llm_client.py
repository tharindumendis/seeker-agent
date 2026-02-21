"""LLM client for interacting with language models."""
import os
from typing import Dict, Any, List, Optional
from time import sleep
import ollama
from ollama._types import ChatResponse


class LLMClient:
    """Client for interacting with LLM via Ollama."""
    
    def __init__(self, model_name: str, temperature: float = 0.7, max_retries: int = 3):
        """
        Initialize LLM client.
        
        Args:
            model_name: Name of the model to use
            temperature: Temperature for generation
            max_retries: Maximum number of retry attempts
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_retries = max_retries
        self.client = ollama.Client()
        
        # Set API key if available
        api_key = os.getenv("OLLAMA_API_KEY")
        if api_key:
            self.client.api_key = api_key
    
    def chat(
        self,
        prompt: str,
        tools: Optional[List] = None,
        expect_json: bool = False,
        temperature: Optional[float] = None
    ) -> ChatResponse:
        """
        Send a chat request to the LLM.
        
        Args:
            prompt: The prompt to send
            tools: List of tools available to the LLM
            expect_json: Whether to expect JSON response
            temperature: Override default temperature
            
        Returns:
            ChatResponse from the LLM
        """
        retry_count = 0
        temp = temperature if temperature is not None else self.temperature
        
        while retry_count <= self.max_retries:
            try:
                # print(f"tools: {tools}")
                response = self.client.chat(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    format="json" if expect_json else None,
                    tools=tools,
                    stream=False,
                    options={"temperature": temp}
                )
                return response
            
            except ollama.ResponseError as e:
                if retry_count < self.max_retries:
                    retry_count += 1
                    wait_time = 2 ** retry_count
                    print(f"⚠️  LLM Error: {e}. Retrying {retry_count}/{self.max_retries} in {wait_time}s...")
                    sleep(wait_time)
                else:
                    raise Exception(f"LLM request failed after {self.max_retries} retries: {e}")
            
            except Exception as e:
                raise Exception(f"Unexpected error in LLM request: {e}")
        
        raise Exception("Max retries exceeded")
    
    def __repr__(self):
        return f"LLMClient(model={self.model_name}, temperature={self.temperature})"
