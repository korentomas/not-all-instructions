"""Run the instruction-retention eval. Models, judges, and per-model settings
live in models.toml (loaded via retention.config); edit that file to change what
runs.

Candidates are swept via ``model=[...]``; the judge panel is fixed via
``model_roles``. The panel is cross-family, so no judge is also a candidate (that
self-judging was the v1 self-bias). The measurement axis is condition in
{baseline, treatment}; the framing arms (treatment_positive / treatment_negation)
run separately via run_framing.py.

Env (keys go in a gitignored .env):
    OPENROUTER_API_KEY=...   # all candidates + the Anthropic judge
    AZUREAI_BASE_URL=https://<resource>.services.ai.azure.com/models   # keyless, via az login
"""

import os

from dotenv import load_dotenv
from inspect_ai import Epochs, eval_set

from retention.config import ablation_judge, build_models, candidates, judges
from retention.retention import instruction_retention
from retention.scorer import retention_mean

# get_model() builds the provider client immediately (needs OPENROUTER_API_KEY),
# which runs BEFORE eval_set auto-loads .env. Load it here so candidate_models()
# can construct clients in a fresh shell without the key pre-exported.
load_dotenv()

CANDIDATES = candidates()
JUDGES = judges()
ABLATION_JUDGE = ablation_judge()


def candidate_models() -> list:
    # RETENTION_ONLY (comma-sep substrings) restricts the sweep to a subset of
    # CANDIDATES. Used to run only the unfinished models into a FRESH log dir:
    # eval-config changes (e.g. a per-model cap) re-hash task identities, so
    # completed logs can't be resumed in the same dir - run the rest separately
    # and merge dirs at analysis time (analyze.py accepts multiple log dirs).
    only = os.environ.get("RETENTION_ONLY")
    models = CANDIDATES
    if only:
        subs = [s.strip() for s in only.split(",") if s.strip()]
        models = [m for m in CANDIDATES if any(s in m for s in subs)]
    return build_models(models)


def main() -> None:
    success, logs = eval_set(
        tasks=[instruction_retention()],
        model=candidate_models(),
        model_roles=JUDGES,
        log_dir=os.environ.get("RETENTION_LOG_DIR", "logs/retention-v2-final"),
        # 5 epochs to average out per-call stochasticity. retention_mean ignores
        # the -1 abstain sentinel, which the default "mean" reducer would average
        # in and which breaks on variable key sets.
        epochs=Epochs(5, reducer=retention_mean()),
        # Each turn re-sends the accumulated ~200K-token context, so a single
        # request can be 3-6x a deployment's per-minute token budget. Keep
        # per-model concurrency low so the big requests are spaced out; if a
        # heavy candidate still wedges, run it in an isolated eval_set
        # (model=[that one], max_connections=2) and merge logs at analysis time.
        max_connections=3,
        # Tasks (one per candidate) run sequentially by default, serializing the
        # whole sweep behind the slowest model. 4-way task parallelism keeps
        # wall-time sane; per-model throttling above still applies.
        max_tasks=4,
        retry_attempts=5,
        # 10 min/request. qwen at ~200K input intermittently wedges on OpenRouter
        # (request sent, no response); a long timeout then stalls the whole sweep
        # for 20 min before retrying. 600s fails a hung request fast so the retry
        # can hit a fresh connection. timeout is excluded from eval_set's task-
        # identity hash, so this is resume-safe.
        timeout=600,
        # Don't let one sample's fatal error abort the whole set. qwen3.5-27b's
        # pymc samples still exceed its 262K window by ~1K even with reasoning
        # stripped (the codebase is the largest; v1 likewise ran qwen on only 2 of
        # 3 codebases). Without this, that error CANCELS the in-flight arviz/bambi
        # samples too. fail_on_error=False isolates the pymc overflow so the rest
        # complete cleanly; pymc-qwen is dropped at analysis.
        fail_on_error=False,
        temperature=0.2,
        # max_tokens intentionally NOT set here - it would override the per-model
        # caps from models.toml applied in candidate_models().
    )
    print("eval_set complete:", success, f"({len(logs)} logs)")


if __name__ == "__main__":
    main()
