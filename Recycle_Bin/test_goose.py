#!/usr/bin/env python3
"""
Test script for Goose AI integration
"""

import sys
import os

# Add the current directory to Python path to import goose_wrapper_fixed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import goose_wrapper_fixed

def test_goose_integration():
    print("Testing Goose AI Integration...")
    
    # Test version check
    print("\n1. Testing version check:")
    version_result = goose_wrapper_fixed.get_version()
    if version_result['success']:
        print(f"Goose AI Version: {version_result['stdout'].strip()}")
    else:
        print(f"Failed to get version: {version_result['stderr']}")
    
    # Test provider listing
    print("\n2. Testing provider listing:")
    providers_result = goose_wrapper_fixed.list_providers()
    if providers_result['success']:
        print(f"Available providers: {providers_result['stdout'].strip()}")
    else:
        print(f"Failed to list providers: {providers_result['stderr']}")
    
    # Test session listing
    print("\n3. Testing session listing:")
    sessions_result = goose_wrapper_fixed.list_sessions()
    if sessions_result['success']:
        print(f"Existing sessions: {sessions_result['stdout'].strip()}")
    else:
        print(f"Failed to list sessions: {sessions_result['stderr']}")

if __name__ == "__main__":
    test_goose_integration()