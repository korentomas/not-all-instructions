# not-all-instructions-bench

**[55 JAIIO / ASAID 2026](https://55jaiio.sadio.org.ar/)** | **[ORCID](https://orcid.org/0009-0002-5682-8475)**

An instruction-retention benchmark for LLM coding assistants, built on
[Inspect AI](https://inspect.aisi.org.uk/).

The setup: take one coding conversation, grow it to about 200K tokens, and plant
12 coding-style rules along the way (use `pytest.mark.parametrize`, don't add new
imports, define constants at module level, and so on). Near the end, ask the model
to write code and check whether it still follows each rule. Some rules stick, some
get forgotten, and at least one gets *worse* once you state it. That uneven decay
is the thing this measures, and it's what a selective-reinforcement scheme would
target instead of repeating every rule every turn.

Code behind *"Not All Instructions Are Forgotten Equal"* (ASAID 2026, 55 JAIIO).
v1 was a one-off runner; v2 is this Inspect port, so anyone can re-run it.

## What it measures

Each probed rule gets a 0-3 compliance score. If the model wrote no relevant code
that turn, the score is -1 (abstain) and dropped from the analysis rather than
averaged in. Two scorers look at every probed turn:

- **Deterministic checkers** (`src/retention/checkers.py`). Regex/AST oracles, the
  primary signal. They read both the fenced code and the `write_file` tool-call
  content, so it doesn't matter where the model put the code. Code that's present
  but breaks the rule scores 0; no relevant code abstains. `CHECKERS_VERSION` pins
  the scoring revision.
- **LLM judge panel** (`judge_panel`). Three judges from different model families,
  scoring the same text. This is the secondary signal, a sanity check on the
  deterministic scores via checker-vs-judge agreement (quadratic-weighted kappa).

No judge shares a model family with any candidate, so nothing grades itself. (In
v1, qwen judged qwen, which biased the panel.)

## Install

    pip install -e .                     # eval only
    pip install -e ".[analysis]"         # + pymc/arviz/pandas for the analysis
    ./scripts/setup_codebases.sh         # clones pymc / arviz-stats / bambi for file injection

## Test

    pytest                 # fast suite (offline, mockllm only, no API keys)
    pytest -m slow         # the MCMC recovery tests (~1 min)

CI (`.github/workflows/test.yml`) runs the fast suite on every push and PR.

## Configure

The default `models.toml` runs every candidate plus the Claude judge through
OpenRouter, and the other two judges (Mistral, Grok) through Azure AI Foundry. So
out of the box you need an OpenRouter key and Azure access. Change the providers by
editing `models.toml`; the `.env` below follows whatever it points at. Inspect loads
`.env` automatically:

    # OpenRouter, for all candidates and the Anthropic judge
    OPENROUTER_API_KEY=sk-or-...
    # Azure AI Foundry. Auth is keyless (Entra ID): `az login` + the "Cognitive
    # Services User" role, so only the endpoint URL goes here, never a key.
    AZUREAI_BASE_URL=https://<resource>.services.ai.azure.com/models

Never commit `.env`.

Which models run, the judge panel, and per-model caps live in `models.toml`, not
in code. Edit that file to add or drop a candidate, swap a judge, or change a
model's `max_tokens`, reasoning handling, or provider routing. `run.py` and
`run_framing.py` read it through `src/retention/config.py`.

The conversations run to ~200K tokens, which is tight for some models. qwen3.5-27b
has a 262K window, not enough to hold the conversation and a complete file write on
the biggest codebase (pymc), so it runs on the other two. `qwen3.5-plus` (1M window,
same family) covers all three. Each model's settings are commented in `models.toml`.

## Run

    python run.py          # main sweep: 6 candidates x {baseline, treatment} x 3 codebases x 5 epochs
    python run_framing.py  # framing arms: 3 candidates x {treatment_positive, treatment_negation}

Both use `eval_set`, so they resume: re-run and it picks up the interrupted sweep
from its log dir. Candidates go in `model=`; the fixed judge panel goes in
`model_roles`.

## Framing experiment

Separate question: does phrasing a rule as a negation hurt retention, with the
meaning held constant? ("don't add new imports" vs "use only existing imports"). The
framing run adds two arms, `treatment_positive` and `treatment_negation`, built from
the treatment templates:

    python scripts/generate_framing_variants.py

For each flippable rule, the instruction clause is swapped for a pure-positive or
pure-negation paraphrase from `data/prompts/instructions.json`. Everything else (the
injected files, the tasks, the test turns, the "Read <module>" tail) stays the same,
so the only thing that changes between arms is the polarity. Three rules can't be
cleanly flipped in English and keep their canonical wording, dropped from the framing
fit. Generation is deterministic and gated by `tests/test_framing.py` (the committed
JSONs must match the builder byte-for-byte); `tests/test_cleanflip.py` checks that the
checkers score the two arms the same way.

## Analyze

    python analyze.py logs/<dir>                       # one run
    python analyze.py logs/<dir> logs/<other-dir>      # merge runs (e.g. a separately-run model)
    python analyze.py logs/<dir> --models v1           # restrict the fit to the 5 v1 candidates

Writes to `analysis-out/`:

- `scores.csv`, the tidy per-(decision, turn, epoch) score matrix.
- `kappa.csv`, quadratic-weighted checker-vs-judge agreement (per judge and panel median).
- `treatment_ranking.csv`, the per-decision treatment effect with 94% HDI, ranked.
  `effective` flags the rules whose HDI excludes zero.
- `variance_components.csv`, the group-level SDs with 94% HDI — heterogeneity by source
  (instruction `sigma_beta`, and the M4 terms `sigma_model` / `sigma_tmodel` / `sigma_codebase`).
- `model_treatment_slopes.csv`, the per-model treatment slope `t_model` (how much each model
  retains when told), ranked; written when more than one model is present.
- `retention_v2.nc`, the saved posterior trace.
- `framing_effect.csv` (+ trace), the per-decision framing effect, when the framing
  logs are in the input.

An example `treatment_ranking.csv` (a development run; the v2 numbers are not frozen):

    decision                       mean   hdi_3%  hdi_97%  effective
    testing_parametrize            +1.35   0.74    2.01    True
    testing_assert_almost          +1.00   0.43    1.62    True
    docs_numpy_style               +0.78   0.18    1.42    True
    dependencies_module_constants  +0.63   0.16    1.07    True
    architecture_extend            +0.08  -0.38    0.59    False
    dependencies_no_new            -0.69  -1.37   -0.10    True

Read it as: stating a rule helps retention for most of the twelve (positive effect,
HDI clears zero), does nothing measurable for a few, and for one it backfires.
`dependencies_no_new` ("don't add new imports") is the only rule with a negative
effect whose HDI excludes zero, the "forgotten worse than never stated" case the
paper is named for. The framing run comes back null (pooled mean 0.12, HDI
[-0.22, 0.45]), so negation phrasing alone does not explain that backfire.

The model in `src/retention/analysis/model.py` is a Bayesian hierarchical
ordered-logistic fit with non-centered per-decision baseline and treatment effects.
When the logs span more than one model/codebase it also fits per-model and per-codebase
baseline intercepts plus a per-model treatment slope (the "M4" spec): model exploration
showed model identity explains as much variance as the instruction type, and that pooling
it away (the old v1 spec) fits markedly worse. See `docs/bayes-model-exploration-v5.md`
for the model comparison, validation, and prior-sensitivity caveat.

## Layout

    src/retention/
      dataset.py    conversations to Inspect Samples
      solver.py     long-context injection + tool loop (the harness)
      scorer.py     deterministic_compliance + judge_panel + epoch reducer
      checkers.py   the 12 ordinal oracles
      framing.py    builds the framing arms (positive/negation paraphrases)
      config.py     reads models.toml into model + judge config
      tracker.py    online BKT tracker (live reinforcement, a minor v2 piece)
      analysis/     score extraction, the ordered-logit, framing effect, kappa
    models.toml     candidates, judges, per-model caps (edit this to change runs)
    run.py          the main sweep
    run_framing.py  the framing arms
    analyze.py      the analysis CLI

## Inspect Evals registry

This lives as a standalone repo for now. Submitting it to
[`inspect_evals`](https://github.com/UKGovernmentBEIS/inspect_evals) is a later step,
once the v2 numbers are frozen. The repo runs on its own in the meantime.

## Citation

If you use this benchmark, please cite the paper:

```bibtex
@inproceedings{korenblit2026notall,
  title     = {Not All Instructions Are Forgotten Equal},
  author    = {Korenblit, Tomas},
  booktitle = {Memorias de las 55 Jornadas Argentinas de Inform{\'a}tica (JAIIO),
               Simposio Argentino de Inteligencia Artificial y Datos (ASAID)},
  year      = {2026},
  month     = aug,
  address   = {La Plata, Argentina},
  publisher = {SADIO},
  issn      = {2451-7496},
  url       = {https://55jaiio.sadio.org.ar/},
  note      = {ORCID 0009-0002-5682-8475},
}
```

## License

Code is MIT (see `LICENSE`). The benchmark data, prompts, and checkers are CC BY
4.0: reuse them freely, but credit the author and cite the paper above.
