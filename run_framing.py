"""Framing run: negation vs positive paraphrases, meaning held constant.

The question: does the negative treatment effect on `dependencies_no_new` come
from the rule's CONTENT (import management is just hard to retain) or its FRAMING
(the negation confuses instruction following)? And the other direction: do the
rules with a clear positive treatment effect (parametrize, module_constants,
standalone) lose adherence when re-phrased as negations?

Two extra arms, built by scripts/generate_framing_variants.py: `treatment_positive`
and `treatment_negation`, identical conversations except the polarity of the
flippable instruction clauses (retention.framing). The contrast is arm vs arm, so
the main sweep (run.py) is untouched.

Models, judges, and per-model caps come from models.toml (the framing run uses a
3-model cross-family subset of the candidates and the same judge panel as run.py).

    python run_framing.py     # resumable; logs -> logs/retention-v2-framing
    python analyze.py logs/retention-v2-framing   # -> framing_effect.csv
"""

import os

from dotenv import load_dotenv
from inspect_ai import Epochs, eval_set

from retention.config import build_models, framing_candidates, judges
from retention.dataset import FRAMING_CONDITIONS
from retention.retention import instruction_retention
from retention.scorer import retention_mean

# get_model() builds the provider client immediately (needs OPENROUTER_API_KEY),
# which runs BEFORE eval_set auto-loads .env. Load it here so candidate_models()
# can construct clients in a fresh shell without the key pre-exported.
load_dotenv()

FRAMING_CANDIDATES = framing_candidates()
JUDGES = judges()


def candidate_models() -> list:
    # RETENTION_ONLY (comma-sep substrings) restricts to a subset - used to run
    # only the unfinished model into a FRESH log dir. See run.py for the note on
    # why config changes orphan completed logs.
    only = os.environ.get("RETENTION_ONLY")
    models = FRAMING_CANDIDATES
    if only:
        subs = [s.strip() for s in only.split(",") if s.strip()]
        models = [m for m in FRAMING_CANDIDATES if any(s in m for s in subs)]
    return build_models(models, profile="framing")


def main() -> None:
    success, logs = eval_set(
        tasks=[instruction_retention(conditions=FRAMING_CONDITIONS)],
        model=candidate_models(),
        model_roles=JUDGES,
        log_dir=os.environ.get("RETENTION_LOG_DIR", "logs/retention-v2-framing"),
        epochs=Epochs(5, reducer=retention_mean()),
        # Same long-context throttling rationale as run.py.
        max_connections=3,
        max_tasks=3,
        retry_attempts=5,
        # 10 min/request - fail wedged qwen long-context requests fast so the
        # retry hits a fresh connection. Resume-safe (timeout is excluded from
        # eval_set's task-identity hash). See run.py for the full note.
        timeout=600,
        temperature=0.2,
        # max_tokens set per-model in models.toml, not globally.
    )
    print("framing eval_set complete:", success, f"({len(logs)} logs)")


if __name__ == "__main__":
    main()
