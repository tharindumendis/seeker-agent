"""Test script for remote input system."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.input_manager import get_user_input
import time


def test_basic_input():
    """Test basic input request."""
    print("=" * 70)
    print("Testing Remote Input System")
    print("=" * 70)
    print("\nThis will request input from both terminal and web interface.")
    print("Whichever responds first wins!\n")
    
    try:
        # Test 1: Simple yes/no question
        response = get_user_input("Do you want to proceed? (y/n)", timeout=60)
        print(f"\n✅ Received response: {response}")
        
        # Test 2: Text input
        name = get_user_input("What is your name?", timeout=60)
        print(f"\n✅ Hello, {name}!")
        
        # Test 3: Number input
        age = get_user_input("What is your age?", timeout=60)
        print(f"\n✅ You are {age} years old!")
        
        print("\n" + "=" * 70)
        print("✅ All tests passed!")
        print("=" * 70)
        
    except TimeoutError as e:
        print(f"\n❌ Timeout: {e}")
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")


if __name__ == "__main__":
    test_basic_input()
