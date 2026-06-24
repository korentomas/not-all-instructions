# experiments-v1 — frozen v1 harness

The original one-off runner behind *"Not All Instructions Are Forgotten Equal"*
(ASAID 2026, 55 JAIIO). The v1 numbers in `../paper/paper.tex` (244 compliance
observations, 5 models, 12 decisions, 3 codebases) come from here.

**This is an archive.** Active work happens in the v2 Inspect port at the repo
root (`../src/retention/`, `../run.py`, `../analyze.py`). v2 re-runs the same
study with proper epochs, a cross-family judge panel, and a framing arm. See the
root `README.md`. Keep this directory for reproducibility of the published v1
figures; do not extend it.

## Layout

| Path | What |
|------|------|
| `config.yaml` | Master config: primary+judge `qwen/qwen3.5-27b`, 4 validation models, seed 42, tracker params, v2/v3 conversation sets. |
| `harness/` | The engine — `runner.py` (turn/tool loop), `tracker.py` (Gaussian-belief BKT tracker), `reinforcer.py` (no/uniform/selective strategies), `checkers.py` (0–3 oracles), `providers.py` (Anthropic/OpenAI/Google/OpenRouter), `tool_executor.py` (read-only repo tools). |
| `prompts/` | System prompts (v1/v2/v3), tool definitions, instruction pools. |
| `conversations/` | Scripted per-codebase conversations. v3 `*_baseline.json` / `*_treatment.json` carry the 12 planted decisions + test turns — the design the paper uses. |
| `scripts/generate_v3_conversations.py` | Generator for the v3 conversation files. |
| `run_phase1.py` / `run_phase2.py` / `run_phase3.py` | Phase drivers (decay / reinforcement strategies / multi-model validation). |
| `analyze.py` | Frequentist decay-curve analysis (separate from the Bayesian fit). |
| `data/` | Experiment output. `phase1/` (Qwen v3 baseline+treatment — the Bayesian fit input) and `phase3/` (multi-model validation) are the **good** runs. `phase1_v0/`, `phase1_v1_broken/`, `phase3_v2_broken/` are discarded earlier attempts (see `phase1_v0/POSTMORTEM.md`). |
| `analysis/` | **The paper's final Bayesian results.** `bayesian_analysis.ipynb` (main fit), `retention_model.nc` (saved posterior), `qwen_sensitivity.{py,nc}` (single-model robustness, r=0.80), `loo_ppc_diagnostics.py`, `figures/` (all 8 paper figures). |
| `codebases/` | The four cloned Bayesian repos used as context fixtures (240M, **git-ignored**). Re-clone with `./setup_codebases.sh`; pinned commits are in `../paper/paper.tex` §Experimental setup. |
| `tests/` | pytest suite for the harness. |

## Reproduce the v1 figures

    pip install -r requirements.txt          # harness deps
    conda env create -f analysis/environment.yml   # pymc/arviz/nutpie for the fit
    ./setup_codebases.sh                      # re-clone the 4 repos at pinned commits
    jupyter lab analysis/bayesian_analysis.ipynb
