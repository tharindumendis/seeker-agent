"""Basic usage examples for Seeker agent."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent import SeekerAgent
from config.settings import Settings


def example_1_simple_task():
    """Example 1: Process a simple task."""
    print("=" * 60)
    print("Example 1: Simple Task Processing")
    print("=" * 60)
    
    # Create agent
    agent = SeekerAgent()
    
    # Process a task
    result = agent.process_task("What is the current time?")
    
    # Display results
    print(f"\nTask completed!")
    print(f"Tool calls: {len(result['tool_results'])}")
    
    return agent


def example_2_file_operations():
    """Example 2: File operations."""
    print("\n" + "=" * 60)
    print("Example 2: File Operations")
    print("=" * 60)
    
    agent = SeekerAgent()
    
    # Create a test file
    result = agent.process_task(
        "Create a file called 'test_output.txt' with the content 'Hello from Seeker!'"
    )
    
    print(f"\nFile operation completed!")
    
    return agent


def example_3_memory_persistence():
    """Example 3: Save and load sessions."""
    print("\n" + "=" * 60)
    print("Example 3: Memory Persistence")
    print("=" * 60)
    
    agent = SeekerAgent()
    
    # Process some tasks
    agent.process_task("Remember that my favorite color is blue")
    agent.process_task("What is 2 + 2?")
    
    # Save session
    session_file = Path(__file__).parent / "test_session.json"
    agent.save_session(str(session_file))
    
    # Create new agent and load session
    new_agent = SeekerAgent()
    new_agent.load_session(str(session_file))
    
    print(f"\nSession loaded! Memory entries: {len(new_agent.memory.memory)}")
    
    return new_agent


def example_4_custom_settings():
    """Example 4: Custom configuration."""
    print("\n" + "=" * 60)
    print("Example 4: Custom Configuration")
    print("=" * 60)
    
    # Create custom settings
    settings = Settings()
    settings.temperature = 0.5
    settings.memory_limit = 5
    
    agent = SeekerAgent(config=settings)
    
    print(f"\nAgent created with custom settings:")
    print(f"  Model: {agent.config.model_name}")
    print(f"  Temperature: {agent.config.temperature}")
    print(f"  Memory Limit: {agent.config.memory_limit}")
    
    return agent


def example_5_tool_inspection():
    """Example 5: Inspect available tools."""
    print("\n" + "=" * 60)
    print("Example 5: Tool Inspection")
    print("=" * 60)
    
    agent = SeekerAgent()
    
    print(f"\nAvailable tools ({len(agent.tool_registry.get_tool_names())}):")
    for tool_name in agent.tool_registry.get_tool_names():
        tool = agent.tool_registry.get_tool(tool_name)
        print(f"\n  • {tool_name}")
        print(f"    Description: {tool.description}")
        
        # Show parameters
        schema = tool.get_schema()
        params = schema['function']['parameters']['properties']
        if params:
            print(f"    Parameters:")
            for param_name, param_info in params.items():
                print(f"      - {param_name} ({param_info['type']}): {param_info.get('description', 'N/A')}")


if __name__ == "__main__":
    print("\n🚀 Seeker Agent - Usage Examples\n")
    
    # Run examples
    try:
        example_1_simple_task()
        example_2_file_operations()
        example_3_memory_persistence()
        example_4_custom_settings()
        example_5_tool_inspection()
        
        print("\n" + "=" * 60)
        print("✓ All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
