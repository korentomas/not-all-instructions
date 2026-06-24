# experiments/harness/tool_executor.py
import re
import subprocess
from pathlib import Path
from harness.providers import ToolCall, ToolResult


DESTRUCTIVE_PATTERNS = ["rm -rf", "rm -r ", "drop table", "push --force", "reset --hard", "clean -fd", "mkfs", "dd if="]


class ToolExecutor:
    """Executes tool calls against a real (read-only) codebase.

    - read_file: returns actual file contents from the repo
    - write_file: logs the write but doesn't modify the repo
    - search_code: runs grep on the repo
    - run_command: returns pre-scripted output (no actual execution)
    """

    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)
        self.files_read: set[str] = set()
        self.files_written: set[str] = set()
        self.write_log: list[dict] = []
        self._scripted_outputs: dict[int, str] = {}

    def set_scripted_output(self, turn: int, output: str):
        self._scripted_outputs[turn] = output

    def load_scripted_outputs(self, outputs: dict[int, str]):
        self._scripted_outputs = outputs

    def execute(self, tool_call: ToolCall, current_turn: int = 0) -> ToolResult:
        name = tool_call.name
        args = tool_call.arguments

        if name == "read_file":
            return self._read_file(tool_call.id, args.get("path", ""))
        elif name == "write_file":
            return self._write_file(tool_call.id, args.get("path", ""), args.get("content", ""))
        elif name == "search_code":
            return self._search_code(tool_call.id, args.get("pattern", ""), args.get("path", ""))
        elif name == "run_command":
            return self._run_command(tool_call.id, args.get("command", ""), current_turn)
        else:
            return ToolResult(
                tool_call_id=tool_call.id,
                name=name,
                content=f"Unknown tool: {name}",
            )

    def _read_file(self, call_id: str, path: str) -> ToolResult:
        file_path = self.repo_root / path
        if not file_path.exists() or not file_path.is_file():
            return ToolResult(
                tool_call_id=call_id,
                name="read_file",
                content=f"Error: File not found: {path}",
            )

        # Security: don't allow path traversal
        try:
            file_path.resolve().relative_to(self.repo_root.resolve())
        except ValueError:
            return ToolResult(
                tool_call_id=call_id,
                name="read_file",
                content=f"Error: Path traversal not allowed: {path}",
            )

        content = file_path.read_text(errors="replace")
        self.files_read.add(path)
        return ToolResult(
            tool_call_id=call_id,
            name="read_file",
            content=content,
        )

    def _write_file(self, call_id: str, path: str, content: str) -> ToolResult:
        self.files_written.add(path)
        self.write_log.append({"path": path, "content": content})
        return ToolResult(
            tool_call_id=call_id,
            name="write_file",
            content=f"Successfully wrote to {path} ({len(content)} characters)",
        )

    def _search_code(self, call_id: str, pattern: str, path: str = "") -> ToolResult:
        search_dir = self.repo_root / path if path else self.repo_root
        try:
            result = subprocess.run(
                ["grep", "-rn", "--include=*.py", pattern, str(search_dir)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            output = result.stdout.strip()
            if not output:
                return ToolResult(tool_call_id=call_id, name="search_code", content="No matches found.")

            # Cap output at 50 lines
            lines = output.split("\n")
            if len(lines) > 50:
                output = "\n".join(lines[:50]) + f"\n... ({len(lines) - 50} more matches)"

            # Make paths relative to repo root
            repo_str = str(self.repo_root) + "/"
            output = output.replace(repo_str, "")

            return ToolResult(tool_call_id=call_id, name="search_code", content=output)
        except subprocess.TimeoutExpired:
            return ToolResult(tool_call_id=call_id, name="search_code", content="Search timed out.")
        except Exception as e:
            return ToolResult(tool_call_id=call_id, name="search_code", content=f"Search error: {e}")

    def _run_command(self, call_id: str, command: str, current_turn: int) -> ToolResult:
        # Block destructive commands
        cmd_lower = command.lower()
        for pattern in DESTRUCTIVE_PATTERNS:
            if pattern in cmd_lower:
                return ToolResult(
                    tool_call_id=call_id,
                    name="run_command",
                    content=f"Blocked: destructive command detected ({pattern}). This command was not executed.",
                )

        # Return scripted output if available
        if current_turn in self._scripted_outputs:
            return ToolResult(
                tool_call_id=call_id,
                name="run_command",
                content=self._scripted_outputs[current_turn],
            )

        # Default: acknowledge execution
        return ToolResult(
            tool_call_id=call_id,
            name="run_command",
            content=f"$ {command}\nCommand executed successfully.",
        )
