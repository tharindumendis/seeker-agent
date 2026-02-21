"""File system tools for Seeker agent."""
import os
from typing import List, Optional, Set
from pathlib import Path
from .base import BaseTool

# Directories that are almost never useful to the agent and inflate output significantly
_DEFAULT_IGNORE_DIRS: Set[str] = {
    ".git", ".svn", ".hg",                        # VCS metadata
    "__pycache__", ".mypy_cache", ".pytest_cache", # Python artifacts
    ".venv", "venv", "env", ".env",                # Virtual envs
    "node_modules", ".next", "dist", "build",      # JS/TS artifacts
    ".idea", ".vscode",                             # IDE config
    "*.egg-info", ".tox",                           # packaging
}

# File extensions to skip (binary / large generated files)
_DEFAULT_IGNORE_EXTS: Set[str] = {
    ".pyc", ".pyo", ".pyd",
    ".so", ".dll", ".exe", ".bin",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico", ".svg",
    ".mp3", ".mp4", ".wav", ".avi",
    ".zip", ".tar", ".gz", ".rar",
    ".db", ".sqlite", ".sqlite3",
    ".lock",  # e.g. poetry.lock, package-lock.json are huge
}

# Hard cap to prevent runaway output
_MAX_ENTRIES = 500


class ReadFileTool(BaseTool):
    """Tool for reading file contents."""

    name = "read_file"
    description = "Read the content of a file with proper encoding handling"
    parameters = {
        "file_path": {
            "type": "string",
            "description": "Absolute or relative path to the file to read",
        }
    }

    def execute(self, file_path: str) -> str:
        """Read file with multiple encoding fallbacks."""
        encodings = [("utf-8", None), ("utf-8", "replace"), ("latin-1", None)]
        for enc, errors in encodings:
            try:
                kwargs = {"encoding": enc}
                if errors:
                    kwargs["errors"] = errors
                with open(file_path, "r", **kwargs) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except Exception as e:
                return f"Error reading file {file_path}: {e}"
        return f"Error reading file {file_path}: could not decode with any supported encoding"


class WriteFileTool(BaseTool):
    """Tool for writing content to files."""

    name = "write_file"
    description = "Write content to a file, creating directories if needed"
    parameters = {
        "file_path": {
            "type": "string",
            "description": "Path where the file should be written",
        },
        "content": {
            "type": "string",
            "description": "Content to write to the file",
        },
    }

    def execute(self, file_path: str, content: str) -> str:
        """Write content to file with directory creation."""
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully wrote to {file_path}"
        except Exception as e:
            return f"Error writing to file {file_path}: {e}"


class ListDirectoryTool(BaseTool):
    """Enhanced tool for listing directory contents with depth control and smart filtering."""

    name = "list_directory"
    description = (
        "List files in a directory tree. Automatically skips noise directories "
        "(.git, __pycache__, node_modules, .venv, etc.) and binary file types. "
        "Returns a compact tree view capped at 500 entries."
    )
    parameters = {
        "directory": {
            "type": "string",
            "description": "Directory path to list",
        },
        "depth": {
            "type": "integer",
            "description": "Maximum depth to traverse (default: 3)",
            "default": 3,
        },
        "show_hidden": {
            "type": "boolean",
            "description": "Include hidden files/dirs (starting with '.') — default: false",
            "default": False,
        },
    }

    def execute(
        self,
        directory: str,
        depth: int = 3,
        show_hidden: bool = False,
    ) -> str:
        path = Path(directory)
        if not path.exists():
            return f"Directory '{directory}' does not exist."
        if not path.is_dir():
            return f"'{directory}' is not a directory."

        lines: List[str] = [f"📁 {directory}  (depth={depth})"]
        counter = [0]  # mutable so nested fn can modify it

        self._walk(path, lines, 0, depth, show_hidden, counter)

        if counter[0] >= _MAX_ENTRIES:
            lines.append(
                f"\n⚠️  Output truncated at {_MAX_ENTRIES} entries. "
                "Use a smaller depth or navigate to a subdirectory."
            )

        lines.append(f"\n{counter[0]} item(s) listed.")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    def _is_ignored_dir(self, name: str, show_hidden: bool) -> bool:
        if not show_hidden and name.startswith("."):
            return True
        return name in _DEFAULT_IGNORE_DIRS

    def _is_ignored_file(self, name: str, show_hidden: bool) -> bool:
        if not show_hidden and name.startswith("."):
            return True
        return Path(name).suffix.lower() in _DEFAULT_IGNORE_EXTS

    def _walk(
        self,
        path: Path,
        lines: List[str],
        current_depth: int,
        max_depth: int,
        show_hidden: bool,
        counter: List[int],
    ) -> None:
        if counter[0] >= _MAX_ENTRIES:
            return

        try:
            items = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except PermissionError:
            lines.append("  " * (current_depth + 1) + "[Permission Denied]")
            return
        except Exception as e:
            lines.append("  " * (current_depth + 1) + f"[Error: {e}]")
            return

        indent = "  " * (current_depth + 1)

        for item in items:
            if counter[0] >= _MAX_ENTRIES:
                break

            if item.is_dir():
                if self._is_ignored_dir(item.name, show_hidden):
                    continue
                lines.append(f"{indent}📂 {item.name}/")
                counter[0] += 1
                if current_depth < max_depth - 1:
                    self._walk(item, lines, current_depth + 1, max_depth, show_hidden, counter)
                else:
                    # Peek: show if there's anything inside
                    try:
                        inner = [
                            c for c in item.iterdir()
                            if not self._is_ignored_dir(c.name, show_hidden)
                            and not self._is_ignored_file(c.name, show_hidden)
                        ]
                        if inner:
                            lines.append(f"{indent}    … ({len(inner)} item(s))")
                    except Exception:
                        pass
            elif item.is_file():
                if self._is_ignored_file(item.name, show_hidden):
                    continue
                try:
                    size = item.stat().st_size
                    size_str = _fmt_size(size)
                except OSError:
                    size_str = "?"
                lines.append(f"{indent}📄 {item.name}  [{size_str}]")
                counter[0] += 1


# ---------------------------------------------------------------------------
def _fmt_size(size: int) -> str:
    """Human-readable file size."""
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.0f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


# ---------------------------------------------------------------------------
# Backward-compat shim
def list_directory(directory: str) -> str:
    """Legacy function for listing directory contents."""
    return ListDirectoryTool().execute(directory)