"""Main entry point for Seeker agent."""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.agent import SeekerAgent
from config.settings import Settings


def main():
    """Main function to run the Seeker agent."""
    # Load settings
    settings = Settings()
    
    # Load from .env if it exists
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        settings.load_from_env_file(str(env_file))
    
    # Create and run agent
    agent = SeekerAgent(config=settings)
    agent.run_interactive()


if __name__ == "__main__":
    main()
