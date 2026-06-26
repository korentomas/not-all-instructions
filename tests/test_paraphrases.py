"""Paraphrase bag (data/prompts/instructions.json) well-formedness.

Guards the experimental manipulation: every flippable decision has >=4 pure-positive
and >=4 pure-negation paraphrases, framing purity holds (positive carries no
prohibition marker; negation carries one), checker_ids are valid, excluded decisions
carry a reason. Purity is what keeps is_negation interpretable.
"""

import json
import re
from pathlib import Path

import pytest

from retention.checkers import check_decision

BAG = json.loads((Path(__file__).resolve().parents[1] / "data" / "prompts" / "instructions.json").read_text())
_PROHIBITION = re.compile(r"\b(don't|do not|never|avoid|no )\b", re.IGNORECASE)

FLIPPABLE = [k for k, v in BAG.items() if not k.startswith("_") and v.get("flippable")]
EXCLUDED = [k for k, v in BAG.items() if not k.startswith("_") and v.get("flippable") is False]


def test_counts():
    assert len(FLIPPABLE) == 9
    assert len(EXCLUDED) == 3


@pytest.mark.parametrize("decision", FLIPPABLE)
def test_flippable_wellformed(decision):
    v = BAG[decision]
    # checker_id must be a real decision the checker knows
    assert check_decision(v["checker_id"], "```python\npass\n```").instruction_type.startswith("decision:")
    pos, neg = v["paraphrases"]["positive"], v["paraphrases"]["negation"]
    assert len(pos) >= 4 and len(neg) >= 4
    for p in pos:
        assert not _PROHIBITION.search(p), f"positive paraphrase not pure: {p!r}"
    for n in neg:
        assert _PROHIBITION.search(n), f"negation paraphrase lacks prohibition: {n!r}"


@pytest.mark.parametrize("decision", EXCLUDED)
def test_excluded_has_reason(decision):
    assert BAG[decision].get("excluded_reason")
