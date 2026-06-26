"""framing arms - builder determinism + arm purity.

The framing contrast γ is only interpretable if the two arms differ ONLY in the
polarity of the flippable instruction clauses. Gates: the committed JSONs are
byte-reproducible from the builder, non-flippable turns are untouched, the
planted instruction is a pure paraphrase of the right polarity from the bag,
and the "Read <module>" tail survives the rebuild.
"""

import json
import re
from pathlib import Path

import pytest

from retention.framing import (
    FRAMING_POLARITIES,
    build_framing_variant,
    flippable_decisions,
    load_bag,
)

ROOT = Path(__file__).resolve().parents[1]
CONV = ROOT / "data" / "conversations"
CODEBASES = ("bambi", "arviz", "pymc")

BAG = load_bag()
FLIPPABLE = set(flippable_decisions(BAG))
_PROHIBITION = re.compile(r"\b(don't|do not|never|avoid|no )\b", re.IGNORECASE)

ARMS = [(cb, pol) for cb in CODEBASES for pol in FRAMING_POLARITIES]


def _canonical(codebase: str) -> dict:
    return json.loads((CONV / f"{codebase}_v3_treatment.json").read_text())


def _arm(codebase: str, polarity: str) -> dict:
    return json.loads((CONV / f"{codebase}_v3_treatment_{polarity}.json").read_text())


@pytest.mark.parametrize("codebase,polarity", ARMS)
def test_committed_files_match_builder(codebase, polarity):
    """Regenerating must be a no-op - the committed arms ARE the builder output."""
    assert _arm(codebase, polarity) == build_framing_variant(_canonical(codebase), polarity, BAG)


@pytest.mark.parametrize("codebase,polarity", ARMS)
def test_only_flippable_turns_differ(codebase, polarity):
    canon, arm = _canonical(codebase), _arm(codebase, polarity)
    assert arm["condition"] == f"treatment_{polarity}"
    for ct, at in zip(canon["turns"], arm["turns"], strict=True):
        planted = ct.get("planted_decision")
        if planted and planted["id"] in FLIPPABLE:
            assert at["content"] != ct["content"]
            # the verbatim "Read ..." tail survives the rebuild
            idx = max(ct["content"].rfind(". Read "), ct["content"].rfind(". Now read "))
            assert at["content"].endswith(ct["content"][idx + 2 :])
        else:
            assert at == ct, f"non-flippable turn {ct['turn']} must be untouched"


@pytest.mark.parametrize("codebase,polarity", ARMS)
def test_planted_instructions_are_pure_bag_paraphrases(codebase, polarity):
    canon_instr = {pd["id"]: pd["instruction"] for pd in _canonical(codebase)["planted_decisions"]}
    for pd in _arm(codebase, polarity)["planted_decisions"]:
        if pd["id"] in FLIPPABLE:
            assert pd["framing"] == polarity
            assert pd["instruction"] in BAG[pd["id"]]["paraphrases"][polarity]
            has_prohibition = bool(_PROHIBITION.search(pd["instruction"]))
            assert has_prohibition == (polarity == "negation"), pd["instruction"]
            # the clause leads the rebuilt turn content
            turn = next(
                t for t in _arm(codebase, polarity)["turns"]
                if t.get("planted_decision", {}).get("id") == pd["id"]
            )
            assert turn["content"].lower().startswith(pd["instruction"].lower())
        else:
            assert pd["framing"] == "excluded"
            assert pd["instruction"] == canon_instr[pd["id"]]


@pytest.mark.parametrize("polarity", FRAMING_POLARITIES)
def test_paraphrase_wording_varies_across_codebases(polarity):
    """PARAPHRASE_PICK gives each codebase a different paraphrase, so γ is not
    hostage to one wording."""
    for decision in FLIPPABLE:
        instrs = {
            next(pd["instruction"] for pd in _arm(cb, polarity)["planted_decisions"]
                 if pd["id"] == decision)
            for cb in CODEBASES
        }
        assert len(instrs) == 3, f"{decision}/{polarity}: expected 3 distinct paraphrases"
