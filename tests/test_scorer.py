"""deterministic scorer: methodological fidelity (NOT numeric reproduction).

The port must score the same text the same way as the reference checkers, on the
same 0-3 scale, over the same 12 decisions. v2 run numbers differ by design.
"""

from inspect_ai import eval as inspect_eval
from inspect_ai.model import ModelOutput, get_model
from inspect_ai.scorer import Score

from retention.checkers import check_decision
from retention.retention import instruction_retention
from retention.scorer import (
    build_scored_text,
    extract_imports,
    retention_mean,
    score_turn_outputs,
)


def test_extract_imports_returns_top_level_modules():
    text = (
        "--- File: a.py ---\n"
        "```python\n"
        "import numpy as np\n"
        "from scipy import stats\n"
        "import os.path\n"
        "```"
    )
    assert extract_imports(text) == {"numpy", "scipy", "os"}


def test_score_turn_outputs_threads_already_imported_context():
    # deps_no_new is context-aware: re-showing an import present in the context
    # the model was given is compliant (3); without context it falls back to the
    # v1 behavior (any import = new = 0).
    test_turns = {20: ["dependencies_no_new"]}
    reshown = {20: "```python\nimport numpy as np\nx = np.sum(a)\n```"}

    v_ctx, _ = score_turn_outputs(reshown, test_turns, already_imported={"numpy"})
    assert v_ctx["dependencies_no_new@20"] == 3

    v_noctx, _ = score_turn_outputs(reshown, test_turns)
    assert v_noctx["dependencies_no_new@20"] == 0


def test_retention_mean_reducer_excludes_sentinel():
    """Epoch reducer: mean per key, -1 excluded, key-union across epochs."""
    reduce = retention_mean()
    out = reduce([
        Score(value={"a@20": 2, "b@20": -1}),   # epoch 1
        Score(value={"a@20": 0, "b@20": 3}),    # epoch 2
    ])
    assert out.value["a@20"] == 1.0             # mean(2, 0)
    assert out.value["b@20"] == 3.0             # -1 excluded, only 3 counts
    # a key that is -1 in every epoch reduces to -1 (no valid value)
    allbad = reduce([Score(value={"c@20": -1}), Score(value={"c@20": -1})])
    assert allbad.value["c@20"] == -1.0

# for-loop over range(len(...)) => broadcasting violated (0); no listcomp => 2
_FORLOOP = "```python\nfor i in range(len(x)):\n    y[i] = x[i] * 2\n```"


def test_scorer_matches_check_decision_directly():
    """Wiring fidelity: scorer path == calling check_decision on the same text."""
    test_turns = {20: ["code_style_broadcasting", "code_style_listcomp"]}
    turn_outputs = {20: _FORLOOP}

    value, _ = score_turn_outputs(turn_outputs, test_turns)

    expected = {
        f"{d}@20": check_decision(d, _FORLOOP).score
        for d in test_turns[20]
    }
    assert value == expected
    # sanity on known checker branches (catches "wrong text wired in")
    assert value["code_style_broadcasting@20"] == 0
    # no collection-transform construct -> checker abstains (-1)
    assert value["code_style_listcomp@20"] == -1


def test_scorer_scale_is_ordinal_0_3():
    # scale is the ordinal 0-3 plus the -1 ABSTAIN sentinel (no opportunity to
    # evaluate the decision); -1 is excluded everywhere downstream.
    test_turns = {20: ["code_style_broadcasting"]}
    for text in [_FORLOOP, "```python\nimport numpy as np\nx.sum()\n```", "no code here"]:
        value, _ = score_turn_outputs({20: text}, test_turns)
        for v in value.values():
            assert v in (-1, 0, 1, 2, 3)


def _mock(n: int = 80):
    return get_model(
        "mockllm/model",
        custom_outputs=[
            ModelOutput.from_content("mockllm/model", "```python\npass\n```")
            for _ in range(n)
        ],
    )


def test_end_to_end_produces_12_key_score():
    """Integration: eval runs solver+scorer, Score.value has 6 turns x 2 decisions."""
    log = inspect_eval(
        instruction_retention(), model=_mock(), limit=1, display="none"
    )[0]
    assert log.status == "success", log.status
    score = log.samples[0].scores["deterministic_compliance"]
    assert isinstance(score.value, dict)
    assert len(score.value) == 12, f"expected 12 (decision,turn) keys, got {len(score.value)}"
    # -1 = abstain (the mock writes a bare `pass`, so most checkers find no
    # opportunity to evaluate); valid ordinal scores are 0-3.
    assert all(v in (-1, 0, 1, 2, 3) for v in score.value.values())


# ── build_scored_text: the scoring-bug fix ──
#
# Models often route their code through the write_file TOOL CALL, not the
# assistant text. The scored text for a turn must be the UNION of the completion
# text and the content of any write_file calls on that turn (each wrapped in a
# fenced python block so check_decision's fenced-code extraction sees it).

# code that the checker can clearly score (numpy ops, no loop -> broadcasting=3)
_WRITE_CODE = "import numpy as np\n\ndef f(x):\n    return np.sum(x)\n"


def test_build_scored_text_writefile_only_turn():
    """Code ONLY in a write_file call -> non-empty scored text containing the code,
    and it scores like real code (not the empty-text flat/abstain gate)."""
    text = build_scored_text("", [{"turn": 20, "path": "f.py", "content": _WRITE_CODE}])
    assert text != ""
    assert "np.sum" in text
    assert "```python" in text  # fenced so the checker extracts it
    # the checker now sees the code: broadcasting (numpy, no loop) scores 3, not abstain
    assert check_decision("code_style_broadcasting", text).score == 3


def test_build_scored_text_text_only_turn():
    """No write_file calls -> the assistant completion is scored as before."""
    completion = "```python\nimport numpy as np\nnp.mean(x)\n```"
    text = build_scored_text(completion, [])
    assert text == completion
    assert check_decision("code_style_broadcasting", text).score == 3


def test_build_scored_text_union_text_and_writes():
    """Both present -> union: completion text AND every write's content included."""
    text = build_scored_text(
        "here is the code",
        [
            {"turn": 20, "path": "a.py", "content": "def a():\n    pass\n"},
            {"turn": 20, "path": "b.py", "content": "def b():\n    pass\n"},
        ],
    )
    assert "here is the code" in text
    assert "def a()" in text
    assert "def b()" in text  # M2: content from every write round survives


def test_build_scored_text_empty_turn_yields_empty():
    """M1: no completion text AND no write content -> "" so the checker abstains
    (we never fabricate text)."""
    assert build_scored_text("", []) == ""
    assert build_scored_text("   \n  ", []) == ""
    assert build_scored_text("", [{"turn": 20, "path": "f.py", "content": "  \n "}]) == ""
    # an empty scored text drives the checker's no-code abstain path (-1)
    assert check_decision("code_style_broadcasting", "").score == -1
