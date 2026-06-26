"""Run-config guard: the judge panel must stay CROSS-FAMILY - no judge shares a
model family with any candidate (the v1 self-bias). Previously enforced only by
comment in run.py; this makes it a failing test.
"""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import run  # noqa: E402
import run_framing  # noqa: E402

# token (any /-_.-separated segment of the model id) -> family
FAMILY_TOKENS = {
    "qwen": "alibaba",
    "nemotron": "nvidia", "nvidia": "nvidia",
    "gemma": "google", "gemini": "google", "google": "google",
    "gpt": "openai", "openai": "openai",
    "llama": "meta", "meta": "meta",
    "kimi": "moonshot", "moonshotai": "moonshot",
    "claude": "anthropic", "anthropic": "anthropic",
    "mistral": "mistral",
    "grok": "xai", "xai": "xai",
    "deepseek": "deepseek",
}


def _family(model: str) -> str:
    tokens = re.split(r"[/_.\-]", model.lower())
    families = {FAMILY_TOKENS[t] for t in tokens if t in FAMILY_TOKENS}
    assert len(families) == 1, f"can't resolve one family for {model!r}: {families} - extend FAMILY_TOKENS"
    return families.pop()


@pytest.mark.parametrize(
    "candidates,judges",
    [
        (run.CANDIDATES, run.JUDGES),
        (run_framing.FRAMING_CANDIDATES, run_framing.JUDGES),
    ],
    ids=["run", "run_framing"],
)
def test_no_judge_shares_family_with_candidate(candidates, judges):
    candidate_families = {_family(m) for m in candidates}
    for role, judge in judges.items():
        assert _family(judge) not in candidate_families, (
            f"{role}={judge} shares a family with a candidate (v1 self-bias)"
        )


def test_ablation_judge_is_deliberately_self_family():
    """The qwen self-judge ablation exists to QUANTIFY self-bias - it must be a
    candidate family, and must not sit in the main panel."""
    (ablation,) = run.ABLATION_JUDGE.values()
    assert _family(ablation) in {_family(m) for m in run.CANDIDATES}
    assert ablation not in run.JUDGES.values()


def test_framing_candidates_are_subset_of_main_sweep():
    assert set(run_framing.FRAMING_CANDIDATES) <= set(run.CANDIDATES)
