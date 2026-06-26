"""Framing variants of the treatment templates: positive vs negation wording.

The framing experiment holds the meaning of each rule constant and varies only
whether it is phrased as a positive ("use only existing imports") or a negation
("don't add new imports"). Two arms are built from each
``{codebase}_v3_treatment.json``:

    treatment_positive - every flippable rule phrased as a pure positive
    treatment_negation - every flippable rule phrased as a pure negation

Both arms rebuild the planted turn from the same minimal template (the paraphrase
clause plus the original "Read <module>" tail). The codebase-justification
sentence is dropped from both, so the only thing that differs between the arms is
the polarity of the instruction. The framing effect (gamma) is estimated arm vs
arm, never against the canonical treatment arm (whose wording differs by more than
polarity).

Three rules can't be cleanly flipped in English; they keep their canonical wording
in both arms, are identical across arms, and are dropped from the framing fit (see
``flippable_decisions``).

Paraphrase choice is deterministic (index ``PARAPHRASE_PICK[codebase]`` into the
bag), so wording varies across codebases while the build stays byte-reproducible.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
BAG_PATH = _ROOT / "data" / "prompts" / "instructions.json"

FRAMING_POLARITIES = ("positive", "negation")
FRAMING_CONDITIONS = tuple(f"treatment_{p}" for p in FRAMING_POLARITIES)

# Deterministic per-codebase paraphrase index: each decision is voiced by a
# different paraphrase in each codebase, so γ is not hostage to one wording.
PARAPHRASE_PICK = {"bambi": 0, "arviz": 1, "pymc": 2}


def load_bag(path: Path = BAG_PATH) -> dict:
    bag = json.loads(path.read_text())
    return {k: v for k, v in bag.items() if not k.startswith("_")}


def flippable_decisions(bag: dict | None = None) -> list[str]:
    bag = bag if bag is not None else load_bag()
    return sorted(k for k, v in bag.items() if v.get("flippable"))


def _read_tail(content: str) -> str:
    """The trailing "Read <module> ..." sentence, kept verbatim in both arms."""
    idx = max(content.rfind(". Read "), content.rfind(". Now read "))
    if idx < 0:
        raise ValueError(f"no 'Read ...' tail in planted turn content: {content!r}")
    return content[idx + 2 :]


def _clause(paraphrase: str) -> str:
    clause = paraphrase[0].upper() + paraphrase[1:]
    return clause if clause.endswith(".") else clause + "."


def build_framing_variant(template: dict, polarity: str, bag: dict | None = None) -> dict:
    """One framing arm from a canonical treatment template (pure function)."""
    if polarity not in FRAMING_POLARITIES:
        raise ValueError(f"polarity must be one of {FRAMING_POLARITIES}, got {polarity!r}")
    if template["condition"] != "treatment":
        raise ValueError("framing variants are built from treatment templates only")
    bag = bag if bag is not None else load_bag()

    out = deepcopy(template)
    out["condition"] = f"treatment_{polarity}"

    pick = PARAPHRASE_PICK[template["codebase"]]
    chosen: dict[str, str] = {}
    for decision_id, spec in bag.items():
        if spec.get("flippable"):
            options = spec["paraphrases"][polarity]
            chosen[decision_id] = options[pick % len(options)]

    for pd in out["planted_decisions"]:
        if pd["id"] in chosen:
            pd["instruction"] = chosen[pd["id"]]
            pd["framing"] = polarity
        else:
            pd["framing"] = "excluded"  # language-irreducible; canonical wording kept

    for turn in out["turns"]:
        planted = turn.get("planted_decision")
        if planted and planted["id"] in chosen:
            tail = _read_tail(turn["content"])
            turn["content"] = f"{_clause(chosen[planted['id']])} {tail}"

    return out


def build_all(conversations_dir: Path) -> list[Path]:
    """Write ``{codebase}_v3_treatment_{positive,negation}.json`` next to each
    canonical treatment template. Returns the written paths."""
    bag = load_bag()
    written: list[Path] = []
    for src in sorted(conversations_dir.glob("*_v3_treatment.json")):
        template = json.loads(src.read_text())
        for polarity in FRAMING_POLARITIES:
            variant = build_framing_variant(template, polarity, bag)
            dst = conversations_dir / f"{template['codebase']}_v3_treatment_{polarity}.json"
            dst.write_text(json.dumps(variant, indent=2) + "\n")
            written.append(dst)
    return written
