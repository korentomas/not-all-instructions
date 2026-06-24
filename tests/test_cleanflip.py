"""Clean-flip gate: a positive-compliant and a negation-compliant response to the
SAME behavioral target must score EQUALLY. If they don't, `is_negation` would be
confounded with a checker-target mismatch (the core concern the framing experiment addresses).

Covers the 6 clean instructions. `testing_parametrize` was DROPPED from the
clean-flip set: the corrected checker scores parametrize USAGE (v1-faithful - 
"use parametrize" is satisfied only by parametrize, so non-parametrized variants
score 0), which is intentionally NOT polarity-symmetric with the negation arm
("don't repeat tests", satisfiable by genuinely-distinct tests). It is therefore
excluded from the framing fit.
The 2 paraphrase-fixable (broadcasting, snake) are gated at the paraphrase level.
The 3 excluded (architecture_extend, code_style_listcomp, docs_numpy_style) are
intentionally NOT here - they are language-irreducible.
"""

import pytest

from retention.checkers import CHECKERS_VERSION, check_decision


def _score(decision: str, code: str) -> int:
    return check_decision(decision, f"```python\n{code}\n```").score


# (decision, positive-compliant code, negation-compliant code) - same behavioral
# target reached two ways. Both must score 3.
CLEAN_FLIP_CASES = [
    (
        "dependencies_no_new",
        "def f(x):\n    return np.sum(x)",          # uses only existing imports
        "def f(x):\n    return sorted(x)",           # adds no import either
    ),
    (
        "testing_assert_almost",
        "def test_a():\n    assert pytest.approx(a) == b",   # approximate
        "def test_a():\n    np.testing.assert_allclose(a, b)",  # not exact ==
    ),
    (
        "naming_underscore",
        "def _helper(x):\n    return x",             # prefixed
        "def _do_work(x):\n    return x",            # not left unprefixed
    ),
    (
        "docs_regex_comments",
        "# match digits\nre.findall(r'\\d+', s)",    # comment above
        "# parse the id\nre.search(r'id=(\\w+)', s)",  # not left uncommented
    ),
    (
        "architecture_standalone",
        "def compute(x):\n    return x * 2",         # standalone fn
        "def run(x):\n    return x + 1",             # no method added to a class
    ),
    (
        "dependencies_module_constants",
        "MAX_ITER = 100\ndef f():\n    return MAX_ITER",   # module constant
        "TOL = 1e-6\ndef g():\n    return TOL",            # no inline magic number
    ),
]


@pytest.mark.parametrize("decision,positive,negation", CLEAN_FLIP_CASES)
def test_positive_and_negation_score_equally(decision, positive, negation):
    sp, sn = _score(decision, positive), _score(decision, negation)
    assert sp == sn == 3, f"{decision}: positive={sp} negation={sn} (must both be 3)"


def test_parametrize_usage_scoring_non_parametrized_is_zero():
    """v1-faithful USAGE scoring: the parametrize test turn asks for many data
    variants of one function, so "use parametrize" is satisfied ONLY by
    parametrize. Non-parametrized tests (even genuinely-distinct ones) score 0,
    NOT 3. This is the corrected instrument and the reason parametrize is no
    longer in the clean-flip set (it is not polarity-symmetric)."""
    distinct = (
        "def test_happy():\n    assert f(2) == 4\n"
        "def test_raises():\n    with pytest.raises(ValueError):\n        f(-1)\n"
    )
    assert _score("testing_parametrize", distinct) == 0


def test_parametrize_v2_still_flags_real_duplication():
    """The fix must NOT make the checker toothless: copy-pasted near-identical
    tests (data-only diff) are exactly what parametrize should replace -> score 0."""
    dup = (
        "def test_add_1():\n    assert add(1, 2) == 3\n"
        "def test_add_2():\n    assert add(4, 5) == 9\n"
    )
    assert _score("testing_parametrize", dup) == 0


def test_checkers_version_pinned():
    assert CHECKERS_VERSION == "5"
