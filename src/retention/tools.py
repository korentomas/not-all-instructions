"""Tools for the retention harness.

Faithful to the reference `ToolExecutor`: `write_file` is LOGGED, never executed
(the repo is read-only). v3 only offers `write_file`, and only on test turns.
Writes are recorded in `store()["writes"]` for the scorer.

Each write is tagged with the turn it happened on (``store()["current_turn"]``,
set by the solver before each test turn's tool loop) so the scorer can recover
per-turn write content both live AND from a saved log - code routed through the
tool call (instead of the assistant text) must still be scored.
"""

from inspect_ai.tool import Tool, tool
from inspect_ai.util import store


@tool
def write_file() -> Tool:
    async def execute(path: str, content: str) -> str:
        """Write or overwrite a file in the repository.

        Args:
            path: Path relative to repo root
            content: Full file content to write
        """
        writes = store().get("writes", [])
        # tag with the current turn so per-turn write content is recoverable both
        # live (solver builds the scored text) and offline (re-scorer reads the log).
        writes.append(
            {"turn": store().get("current_turn"), "path": path, "content": content}
        )
        store().set("writes", writes)
        # same confirmation string as the reference ToolExecutor._write_file
        return f"Successfully wrote to {path} ({len(content)} characters)"

    return execute
