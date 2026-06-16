"""solver smoke test against mockllm (no API cost).

Verifies the harness replays all turns, accumulates the conversation, and stores
per-test-turn outputs + files_read. Does NOT check compliance.
"""

from inspect_ai import eval as inspect_eval
from inspect_ai.model import ModelOutput, get_model

from retention.retention import instruction_retention


def _mock(n: int = 80):
    # one canned code response per generate call (26 turns, no tool calls)
    return get_model(
        "mockllm/model",
        custom_outputs=[
            ModelOutput.from_content("mockllm/model", "```python\npass\n```")
            for _ in range(n)
        ],
    )


def test_solver_runs_full_conversation():
    log = inspect_eval(
        instruction_retention(), model=_mock(), limit=1, display="none"
    )[0]
    assert log.status == "success", log.status
    sample = log.samples[0]

    # 26 turns -> 26 assistant messages + 26 user + 1 system
    assistant = [m for m in sample.messages if m.role == "assistant"]
    assert len(assistant) == 26, f"expected 26 assistant turns, got {len(assistant)}"

    # outputs captured at the 6 test turns
    turn_outputs = sample.store["turn_outputs"]
    assert len(turn_outputs) == 6, f"expected 6 scored turns, got {len(turn_outputs)}"

    # files_read is populated (templates inject files on context turns)
    assert isinstance(sample.store["files_read"], list)


# ── the scoring-bug fix: code routed through the write_file TOOL CALL ──

# decision-relevant code the checker can clearly score (numpy ops, no loop)
_TOOL_CODE = "import numpy as np\n\ndef f(x):\n    return np.sum(x)\n"


def _tool_routing_mock():
    """Callable mock: on a TEST turn (write_file offered) the model routes its code
    through a write_file TOOL CALL and emits NO assistant text; otherwise it replies
    with plain text. The second round of a test turn (tool result already present)
    returns empty text to end the loop. This reproduces the bug class (gpt-oss /
    gemini / gemma / qwen route code to the tool)."""

    def outputs(input, tools, tool_choice, config):
        offers_write = any(t.name == "write_file" for t in tools)
        # already executed the write this turn? (a tool message is the last input)
        already_wrote = input and input[-1].role == "tool"
        if offers_write and not already_wrote:
            return ModelOutput.for_tool_call(
                "mockllm/model",
                tool_name="write_file",
                tool_arguments={"path": "solution.py", "content": _TOOL_CODE},
            )
        if offers_write and already_wrote:
            return ModelOutput.from_content("mockllm/model", "")  # no trailing text
        return ModelOutput.from_content("mockllm/model", "done")

    return get_model("mockllm/model", custom_outputs=outputs)


def test_writefile_tool_code_is_scored():
    """A test turn whose code lives ONLY in a write_file tool call (empty assistant
    text) must produce non-empty scored text that contains that code - the bug was
    that this text was empty, so the checker gate returned a flat/abstain score."""
    log = inspect_eval(
        instruction_retention(), model=_tool_routing_mock(), limit=1, display="none"
    )[0]
    assert log.status == "success", log.status
    sample = log.samples[0]

    # writes are tagged with their turn (live + recoverable from the saved log)
    writes = sample.store["writes"]
    assert writes, "expected write_file calls to be recorded"
    assert all("turn" in w for w in writes), "each write must be turn-tagged"

    # every test turn's scored text is non-empty and contains the tool-call code
    turn_outputs = sample.store["turn_outputs"]
    assert len(turn_outputs) == 6
    for text in turn_outputs.values():
        assert text != "", "tool-call code must not produce empty scored text"
        assert "np.sum" in text

    # and it actually scores like real code, not the empty-text abstain
    score = sample.scores["deterministic_compliance"].value
    assert score["code_style_broadcasting@20"] == 3
