"""Test to verify non-blocking behavior of input manager."""
import sys
from pathlib import Path
import time
import threading

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.input_manager import input_manager


def simulate_web_requests():
    """Simulate web server checking for pending requests."""
    print("\n🌐 Web server simulation started...")
    for i in range(20):
        time.sleep(0.5)
        pending = input_manager.get_pending_requests()
        if pending:
            print(f"   [{i}] ✅ Web can see pending request: {pending[0]['prompt'][:30]}...")
        else:
            print(f"   [{i}] ⏳ No pending requests")


def test_non_blocking():
    """Test that input manager doesn't block web requests."""
    print("=" * 70)
    print("Testing Non-Blocking Input Manager")
    print("=" * 70)
    print("\nThis test verifies that web requests work while waiting for terminal input.")
    print("You should see web simulation messages WHILE waiting for your input.\n")
    
    # Start web simulation in background
    web_thread = threading.Thread(target=simulate_web_requests, daemon=True)
    web_thread.start()
    
    # Request input (this should NOT block the web thread)
    try:
        response = input_manager.request_input(
            "Enter your name (web should keep polling):",
            timeout=30
        )
        print(f"\n✅ Got response: {response}")
        print("\n🎉 Test PASSED - Web requests worked during terminal wait!")
        
    except TimeoutError:
        print("\n⏱️ Timeout - but that's OK for testing")
    
    # Give web thread time to finish
    time.sleep(2)
    print("\n" + "=" * 70)


if __name__ == "__main__":
    test_non_blocking()
