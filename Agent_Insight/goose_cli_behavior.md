# Goose CLI Behavior and Interface

## Session Management
- Goose maintains session state in JSONL files (e.g., `C:\Users\thari\.config\goose\sessions\y8v6.jsonl`)
- When resuming a session, it continues from where it left off
- The interface uses a "G❯" prompt when ready for input

## CLI Interaction
- Uses `goose session start <name>` to start or resume a session
- When starting a session that already exists, it prompts whether to overwrite or resume
- Interactive interface that waits for user input after initialization

## Provider Information
- Ollama provider is marked as experimental with a caution to "use with care"
- Multiple LLM providers supported (based on previous findings)

## Interface Behavior
- After starting/resuming a session, displays "starting session | name: y8v6  profile: default"
- Then shows the interactive prompt "G❯" where commands can be entered