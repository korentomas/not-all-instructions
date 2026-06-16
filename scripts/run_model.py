"""Run ONE candidate model through the full task (both conditions, 3 codebases,
5 epochs) with the canonical judge panel. For filling individual candidates from
a separate shell without touching other runs.

Usage:
    cd not-all-instructions
    # .env (OPENROUTER_API_KEY + AZUREAI_BASE_URL) is auto-loaded by Inspect;
    # the grok judge also needs `az login` (keyless).
    python scripts/run_model.py openrouter/moonshotai/kimi-k2.6
    python scripts/run_model.py openrouter/nvidia/nemotron-3-super-120b-a12b --conn 8

Logs land in logs/retention-v2-<short-model-name>/ and merge at analysis time:
    python analyze.py logs/retention-v2 logs/retention-v2-*
"""

import argparse

from inspect_ai import Epochs, eval_set

from retention.retention import instruction_retention
from retention.scorer import retention_mean

# Canonical cross-family judge panel (must match run.py JUDGES).
JUDGES = {
    "judge_1": "openrouter/anthropic/claude-haiku-4.5",
    "judge_2": "openrouter/mistralai/mistral-medium-3.1",
    "judge_3": "azureai/grok-4.3",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("model", help="provider/model id, e.g. openrouter/moonshotai/kimi-k2.6")
    ap.add_argument("--conn", type=int, default=6, help="max_connections (OpenRouter handles 6-10)")
    args = ap.parse_args()

    short = args.model.split("/")[-1]
    success, logs = eval_set(
        tasks=[instruction_retention()],
        model=[args.model],
        model_roles=JUDGES,
        log_dir=f"logs/retention-v2-{short}",
        epochs=Epochs(5, reducer=retention_mean()),
        max_connections=args.conn,
        retry_attempts=4,
        timeout=1200,
        temperature=0.2,
        max_tokens=1024,
    )
    print(f"{short}: complete={success} ({len(logs)} logs)")


if __name__ == "__main__":
    main()
