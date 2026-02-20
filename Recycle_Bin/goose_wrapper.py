#!/usr/bin/env python3
"""
Goose AI Wrapper Script for Seeker AI Integration
Created by Seeker AI Agent on February 16, 2026

This script provides a Python interface to interact with the Goose AI agent,
enabling communication between Seeker and Goose for collaborative task execution.
"""

import subprocess
import sys
import os
import json

def run_goose_command(command_args):
    """Execute a Goose command and return the result"""
    try:
        # Construct the full command
        cmd = ['goose'] + command_args
        
        # Execute the command
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        
        # Return structured result
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode
        }
    except FileNotFoundError:
        return {
            'success': False,
            'stdout': '',
            'stderr': 'Goose command not found. Please ensure Goose AI is properly installed.',
            'return_code': -1
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': f'Error executing command: {str(e)}',
            'return_code': -1
        }

def list_providers():
    """List available LLM providers"""
    return run_goose_command(['providers'])

def list_sessions():
    """List existing Goose sessions"""
    return run_goose_command(['session', 'list'])

def start_session(session_name, provider=None):
    """Start a new Goose session"""
    cmd = ['session', 'new', session_name]
    if provider:
        cmd.extend(['--provider', provider])
    return run_goose_command(cmd)

def send_message(session_name, message):
    """Send a message to a Goose session"""
    return run_goose_command([message])

def end_session(session_name):
    """End a Goose session"""
    return run_goose_command(['session', 'stop', session_name])

def get_version():
    """Get Goose version"""
    return run_goose_command(['--version'])

def main():
    """Main function for testing the wrapper"""
    print("Goose AI Wrapper for Seeker AI")
    print("=" * 30)
    
    # Test Goose version
    print("\n1. Testing Goose version...")
    version_result = get_version()
    if version_result['success']:
        print(f"Goose Version: {version_result['stdout'].strip()}")
    else:
        print(f"Failed to get Goose version: {version_result['stderr']}")
        return
    
    # List providers
    print("\n2. Listing available providers...")
    providers_result = list_providers()
    if providers_result['success']:
        print("Available Providers:")
        print(providers_result['stdout'])
    else:
        print(f"Failed to list providers: {providers_result['stderr']}")
    
    # List sessions
    print("\n3. Listing existing sessions...")
    sessions_result = list_sessions()
    if sessions_result['success']:
        print("Existing Sessions:")
        print(sessions_result['stdout'])
    else:
        print(f"No existing sessions or failed to list sessions: {sessions_result['stderr']}")

if __name__ == "__main__":
    main()