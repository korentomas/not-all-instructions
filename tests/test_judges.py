"""judge panel judge panel wiring (mockllm judges, no API cost).

3 cross-family judges rate each (decision, test_turn). Per-judge scores land in
Score.value. Real judges + κ come later (offline); here we validate the panel
fans out correctly and parses ordinal replies.
"""

from inspect_ai import eval as inspect_eval
from inspect_ai.model import ModelOutput, get_model

from retention.prompts import INSTRUCTION_TEXT
from retention.retention import instruction_retention
from retention.scorer import JUDGE_ROLES, _parse_judge_score


def test_instruction_text_covers_12_decisions():
    assert len(INSTRUCTION_TEXT) == 12


def test_parse_judge_score():
    # strict: a lone 0-3 token (optional whitespace/quotes/period) parses
    assert _parse_judge_score("2") == 2
    assert _parse_judge_score(" 3 ") == 3
    assert _parse_judge_score("2.") == 2
    assert _parse_judge_score('"0"') == 0
    # anything else is UNPARSEABLE (-1) - never silently mis-scored
    assert _parse_judge_score("10") == -1          # was mis-parsed as 1
    assert _parse_judge_score("2024") == -1        # was mis-parsed as 2
    assert _parse_judge_score("8/10") == -1        # was mis-parsed as 1
    assert _parse_judge_score("Score: 3") == -1    # prose → unparseable
    assert _parse_judge_score("nonsense") == -1
    assert _parse_judge_score("") == -1


def _candidate_mock(n: int = 80):
    return get_model(
        "mockllm/model",
        custom_outputs=[
            ModelOutput.from_content("mockllm/model", "```python\npass\n```")
            for _ in range(n)
        ],
    )


def _judge_mock(reply: str = "2", n: int = 300):
    return get_model(
        "mockllm/model",
        custom_outputs=[ModelOutput.from_content("mockllm/model", reply) for _ in range(n)],
    )


def test_judge_panel_fans_out_36_keys():
    log = inspect_eval(
        instruction_retention(),
        model=_candidate_mock(),
        model_roles={r: _judge_mock() for r in JUDGE_ROLES},
        limit=1,
        display="none",
    )[0]
    assert log.status == "success", log.status

    panel = log.samples[0].scores["judge_panel"].value
    # 3 judges x 6 test turns x 2 decisions = 36
    assert len(panel) == 36, f"expected 36 judge scores, got {len(panel)}"
    assert all(v == 2 for v in panel.values())
    # both channels present
    assert "deterministic_compliance" in log.samples[0].scores
