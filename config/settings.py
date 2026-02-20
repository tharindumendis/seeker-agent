"""Configuration management for Seeker agent."""
import os
from pathlib import Path
from typing import Optional


class Settings:
    """Central configuration for the Seeker agent."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.cache_dir = self.project_root / "cache"
        self.logs_dir = self.project_root / "logs"
        self.sessions_dir = self.logs_dir / "sessions"
        
        # LLM Configuration
        self.model_name = os.getenv("SEEKER_MODEL", "qwen3-coder:480b-cloud")
        self.temperature = float(os.getenv("SEEKER_TEMPERATURE", "0.7"))
        self.max_retries = int(os.getenv("SEEKER_MAX_RETRIES", "3"))
        
        # Memory Configuration
        self.memory_limit = int(os.getenv("SEEKER_MEMORY_LIMIT", "10"))
        self.history_limit = int(os.getenv("SEEKER_HISTORY_LIMIT", "50"))
        
        # API Keys
        self.ollama_api_key = os.getenv("OLLAMA_API_KEY")
        
        # Ensure directories exist
        self.cache_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.sessions_dir.mkdir(exist_ok=True)
    
    def load_from_env_file(self, env_path: Optional[str] = None):
        """Load environment variables from .env file."""
        if env_path is None:
            env_path = self.project_root / ".env"
        
        if not os.path.exists(env_path):
            return
        
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        
        # Reload settings after loading env file
        self.__init__()
    
    def __repr__(self):
        return (
            f"Settings(model={self.model_name}, "
            f"temperature={self.temperature}, "
            f"memory_limit={self.memory_limit})"
        )
