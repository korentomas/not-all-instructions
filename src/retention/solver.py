"""Multi-turn solver - faithful port of `ConversationRunner` (version=3 path).

Replays the scripted conversation: each turn injects file contents into the user
message (planted instructions already live in `turn["content"]`), then calls the
candidate model. `write_file` is offered only on test turns. The conversation
accumulates in `state.messages` (this is where context grows to ~200K).

Reinforcement is OFF here (the reference v3 runs used `NoReinforcement`). The BKT
selective-reinforcement path is a separate add-on.

Mirrors `runner.py`:
- `MAX_INJECT_CHARS = 40000`, same truncation format.
- `MAX_TOOL_ROUNDS = 3`, same `_send_with_tool_loop` shape.
- v3 `_get_tools_for_turn`: only `write_file`, only on turns with `tests_decisions`.
"""

from __future__ import annotations

from pathlib import Path

from inspect_ai.model import (
    ChatMessageSystem,
    ChatMessageUser,
    Model,
    execute_tools,
    get_model,
)
from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.util import store

from retention.scorer import build_scored_text
from retention.tools import write_file

_ROOT = Path(__file__).resolve().parents[2]
SYSTEM_PROMPT = (_ROOT / "data" / "prompts" / "system_prompt_v3.txt").read_text()

MAX_INJECT_CHARS = 40000  # matches runner.ConversationRunner.MAX_INJECT_CHARS
MAX_TOOL_ROUNDS = 3       # matches runner.MAX_TOOL_ROUNDS


def _inject_context(turn: dict, repo_root: Path, files_read: set[str]) -> str:
    """Pre-inject file contents into the user message (runner._inject_context).

    These v3 templates use only `inject_files` (no inject_search, no scripted
    outputs), so we port exactly that branch.
    """
    parts = [turn["content"]]
    for file_path in turn.get("inject_files", []):
        full_path = repo_root / file_path
        if full_path.exists():
            content = full_path.read_text(errors="replace")
            if len(content) > MAX_INJECT_CHARS:
                truncated = content[:MAX_INJECT_CHARS].rsplit("\n", 1)[0]
                total_lines = content.count("\n")
                shown_lines = truncated.count("\n")
                content = truncated + f"\n\n... (truncated: showing {shown_lines}/{total_lines} lines)"
            parts.append(f"\n\n--- File: {file_path} ---\n```python\n{content}\n```")
            files_read.add(file_path)
        else:
            parts.append(f"\n\n--- File: {file_path} --- (not found)")
    return "\n".join(parts)


async def _send_with_tool_loop(model: Model, messages: list, turn_tools: list):
    """Faithful port of runner._send_with_tool_loop. Returns final text output."""
    for _ in range(MAX_TOOL_ROUNDS + 1):
        out = await model.generate(messages, tools=turn_tools)
        if not out.message.tool_calls:
            return out
        messages.append(out.message)  # assistant message with tool calls
        exec_result = await execute_tools([out.message], turn_tools)
        messages.extend(exec_result.messages)
    # rounds exhausted - force a final text response with no tools
    out = await model.generate(messages, tools=[])
    if out.message.tool_calls:
        # defensive: a provider ignored the empty tool list and still emitted
        # tool_calls. Resolve them once so the trailing assistant message has no
        # dangling tool_use (which would make the next turn's user message a
        # malformed sequence), then take the text reply.
        messages.append(out.message)
        exec_result = await execute_tools([out.message], turn_tools)
        messages.extend(exec_result.messages)
        out = await model.generate(messages, tools=[])
    return out


@solver
def retention_harness() -> Solver:
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        meta = state.metadata
        repo_root = _ROOT / "data" / meta["repo_path"]
        candidate = get_model(role="candidate", default=get_model())

        files_read: set[str] = set()
        turn_outputs: dict[int, str] = {}

        # rebuild the conversation from scratch (scripted turns drive everything)
        state.messages = [ChatMessageSystem(content=SYSTEM_PROMPT)]

        for turn in meta["turns"]:
            content = _inject_context(turn, repo_root, files_read)
            state.messages.append(ChatMessageUser(content=content))

            is_test = bool(turn.get("tests_decisions"))
            turn_tools = [write_file()] if is_test else []

            # tag any write_file calls in this turn's tool loop with the turn number
            # (the tool reads this from the store; see tools.write_file).
            if is_test:
                store().set("current_turn", turn["turn"])

            out = await _send_with_tool_loop(candidate, state.messages, turn_tools)
            state.messages.append(out.message)
            state.output = out

            if is_test:
                # M2: include write_file content from EVERY tool round of this turn,
                # not just the final text - code routed to the tool must not be lost.
                turn_writes = [
                    w for w in store().get("writes", [])
                    if w.get("turn") == turn["turn"]
                ]
                turn_outputs[turn["turn"]] = build_scored_text(out.completion, turn_writes)

        store().set("files_read", sorted(files_read))
        store().set("turn_outputs", turn_outputs)
        return state

    return solve
