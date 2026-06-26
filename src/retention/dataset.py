"""Dataset loader for the instruction-retention benchmark.

One conversation template = one Inspect ``Sample``. A template is
a scripted multi-turn coding session that grows to ~200K tokens; the planted
instructions are scored at the ``test_turns``. Replication across runs is handled
by Inspect ``epochs``, not by duplicating templates here.

Source of truth (for now) is ``experiments/conversations/*_v3_*.json`` - the same
files the reference harness uses, so scoring parity compares like-for-like.
"""

from __future__ import annotations

import json
from pathlib import Path

from inspect_ai.dataset import MemoryDataset, Sample

# repo root = .../not-all-instructions  (dataset.py -> retention -> src -> root)
_ROOT = Path(__file__).resolve().parents[2]
CONVERSATIONS_DIR = _ROOT / "data" / "conversations"

CODEBASES = ("bambi", "arviz", "pymc")
# v3 measurement axis (channel B). Reinforcement axis lives elsewhere (BKT mini-demo).
CONDITIONS = ("baseline", "treatment")
# framing arms (pure-positive vs pure-negation paraphrases of the flippable
# decisions; see retention.framing). Run via run_framing.py, not the main sweep.
FRAMING_CONDITIONS = ("treatment_positive", "treatment_negation")


def _conversation_to_sample(path: Path) -> Sample:
    d = json.loads(path.read_text())

    # turn number -> list of decision ids scored at that turn
    test_turns: dict[int, list[str]] = {
        tt["turn"]: tt["tests_decisions"] for tt in d.get("test_turns", [])
    }

    return Sample(
        input=d["task_description"],
        id=f"{d['codebase']}_{d['condition']}",
        metadata={
            "codebase": d["codebase"],
            "repo_path": d["repo_path"],
            "condition": d["condition"],
            # baseline has [] planted_decisions but the same test_turns (spontaneous compliance)
            "planted_decisions": d.get("planted_decisions", []),
            "test_turns": test_turns,
            "turns": d["turns"],
        },
    )


def retention_dataset(
    *,
    conditions: tuple[str, ...] = CONDITIONS,
    codebases: tuple[str, ...] = CODEBASES,
    conversations_dir: Path = CONVERSATIONS_DIR,
) -> MemoryDataset:
    """Load conversation templates into a MemoryDataset.

    Returns one Sample per ``{codebase}_v3_{condition}.json`` that exists.
    """
    samples: list[Sample] = []
    for codebase in codebases:
        for condition in conditions:
            path = conversations_dir / f"{codebase}_v3_{condition}.json"
            if path.exists():
                samples.append(_conversation_to_sample(path))
    if not samples:
        raise FileNotFoundError(
            f"No conversation templates found in {conversations_dir}"
        )
    return MemoryDataset(samples)
