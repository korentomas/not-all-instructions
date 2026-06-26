# Not All Instructions Are Forgotten Equal

Code and data for the paper *Not All Instructions Are Forgotten Equal*
(55 JAIIO / ASAID 2026), which measures how language models retain individual
user-stated instructions over long multi-turn coding sessions.

## Layout

- `paper/` — LaTeX source, compiled PDF, and figures.
- `experiments-v1/` — the study behind the camera-ready paper: the harness,
  prompts, conversation data, and `analysis/` (the Bayesian notebook, the
  figure scripts, and `retention_model.nc`, the saved trace). Everything the
  paper reports can be regenerated from here.
- `src/`, `run.py`, `analyze.py`, `models.toml` — a later re-implementation on
  Inspect AI, used for the re-run and the extended analysis.
- `reanalysis/` — post-acceptance measurement audit: re-scoring / re-judging
  tooling and the re-scored result tables. This feeds the extended paper and is
  **not** the source of the camera-ready numbers.
- `logs/`, `data/` — run logs and conversation data.

## Reproducing the paper figures

```
cd experiments-v1/analysis
python make_paper_ppc.py            # Fig 1  posterior predictive check
python make_paper_forest.py         # Fig 2  per-instruction treatment effects
python make_paper_policy.py         # Fig 3  reinforcement priorities
python make_paper_ppc_decision.py   # Fig 4  per-decision posterior predictive
```

All four read `retention_model.nc` and write to `../../paper/figures/`.

## Notes

- The three target codebases (Bambi, ArviZ, PyMC) are not vendored here; the
  pinned commits are listed in the paper's Experimental setup section.
- The large extended-analysis traces (the model ladder) exceed GitHub's
  100 MB file limit and are archived separately for the extended paper.

## License

Code under MIT, data under CC BY 4.0; see `LICENSE`.
