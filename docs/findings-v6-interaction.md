# Findings v6 — the interaction model, clean re-analysis, and the eval-methodology angle

Date: 2026-06-25. Supersedes the model-effect conclusions in `bayes-model-exploration-v5.md`
and `deep-dive-findings-v5.md` where they disagree (those used a contaminated 10-model pool
and/or the additive M4; this note uses the principled v1-5 set and adds the interaction model).

This is the consolidated record behind the **extended retention paper** (study A) and the
**eval-methodology paper** (study B). All fits are PyMC ordered-logistic on `logs/rescored-v5`
(CHECKERS_VERSION 5), `--models v1` (the 5 published models) unless noted. Traces in
`analysis-out-v1/`. 0 divergences except where noted; all R-hat = 1.0.

## 0. Why a clean re-analysis

The first v2 fit used `analyze.py` default `--models all` = **10 merged models**, including
`gpt-oss-120b` (baseline n=5, unusable), `llama-3.3-70b` (Azure, sparse/dup of the OpenRouter
`-instruct`), `deepseek-v3.2` and `qwen3.5-plus` (not in the declared candidate set). The
variance-component estimates are pool-sensitive (psense flags them as prior-influenced — few
groups). So the model-effect numbers in the v5 docs are not trustworthy as stated. The
principled primary set is `--models v1` (qwen3.5-27b, nemotron-3-super-120b, gemma-4-26b,
gemini-3.1-flash-lite, gpt-5.4-nano) — all have baseline+treatment in v2, directly comparable
to the published paper. 1067 main observations (baseline+treatment), 12 decisions, 5 models, 3
codebases, 5 epochs.

## 1. Model-set sensitivity (the headline caveat)

Same M4 spec, three model pools:

| pool | σ_β (instruction) | σ_model | σ_tmodel |
|---|---|---|---|
| v1 (5 models) | 1.19 [0.55, 1.99] | 0.48 [0.01, 1.02] | 0.52 [0, 1.16] |
| candidate (6) | 1.68 [0.74, 2.77] | 0.98 [0.05, 2.25] | 0.87 [0, 2.25] |
| all (10) | 1.02 [0.51, 1.55] | 0.92 [0.47, 1.43] | 0.84 [0.36, 1.41] |

**σ_β (instruction heterogeneity) is the stable, robust quantity (~1.0-1.7, always excludes 0).
The model variance components are NOT stable** — they jump with the pool. The "model matters as
much as instruction" claim in the v5 docs is an artifact of the additive decomposition on a
particular pool; it does not survive (see §2).

## 2. The model ladder (clean v1-5, one process, valid LOO)

Ordered-logit cumulative link, non-centered REs, offset cutpoints, target_accept 0.99.

| model | structure | elpd_loo | Δelpd (dse) | weight | div |
|---|---|---|---|---|---|
| **M8** | M4 + model×decision interaction variance `z_{m,d}~N(0,σ_int)` | **−545.9** | 0 | 0.62 | 0 |
| M_irt | explanatory 2PL/GRM: discrimination `a_d·θ_model` | −555.4 | 9.5 (10.5) | 0.38 | 0 |
| M_corr | M4 + LKJ-correlated per-model [intercept, slope] | −604.4 | 58.5 (11.2) | ~0 | 2 |
| M4 | per-decision α/β + per-model intercept+slope + per-codebase intercept (additive) | −604.8 | 58.9 (11.2) | ~0 | 0 |
| M0 | per-decision α/β only (the v1 published model) | −607.2 | 61.3 (11.7) | ~0 | 0 |

**Conclusions:**
- **The model×instruction interaction is the dominant structural feature.** Both models that
  capture it (M8 variance-component; M_irt multiplicative discrimination) beat every additive
  model by ~59 ELPD (5+ SE). M8 vs M_irt differ by only 9.5 ± 10.5 (within ~1 SE): the
  *interaction* matters, not its exact parameterization.
- **Additive model terms add nothing.** M4 (per-model main effect + slope) ≈ M0 (Δ2.4,
  indistinguishable). This is consistent with the published paper's hedged finding-3 ("little
  evidence model/codebase explains variance") — the additive model main effect is genuinely
  negligible. What the v5 docs called "model matters" is the *interaction*, mis-attributed to
  additive terms.
- **Responsiveness does not track baseline compliance.** M_corr intercept–slope correlation
  = −0.37 [−0.97, 0.35] (crosses 0). A model that complies by default is not necessarily more
  reinforceable.
- M8 `σ_int = 1.84` [1.26, 2.40] — dominates σ_β (0.43), σ_model (0.66), σ_tmodel (0.43) once
  the interaction is in the model (the additive components shrink because they were absorbing
  interaction variance).

**M8 is the recommended canonical model**: best ELPD, fully identified (a Normal(0,σ) interaction
has none of the rank-1 factor model's sign/scale/rotation indeterminacy — M7 failed at R-hat
1.74; M8 converges clean), interpretable σ_int + per-cell z, 0 divergences.

## 3. What is robust (survives every cut)

- **Heterogeneity is real:** σ_β excludes 0 in every pool and model.
- **The v1 "backfire" is a measurement artifact, two independent ways:**
  - checker fix: `dependencies_no_new` β goes −2.36 (v1) → +0.05 (v5 fixed) → −0.11/−0.25 (clean
    M0/M4); null in every v2 fit.
  - framing: pooled γ (negation − positive) = 0.36 [−0.13, 0.89], all decisions cross 0 →
    negation phrasing is NOT the cause. Diagnostic: M_irt gives `dependencies_no_new` the
    highest discrimination (a=2.90) — the artifact item separates models most, a caution that
    high IRT discrimination ≠ construct validity.
- **Per-decision rankings are stable across M0/M4** (the heterogeneity is not a model artifact);
  7 effective on clean v1-5 (module_constants, regex_comments, numpy_style, parametrize,
  architecture_extend, naming_underscore, architecture_standalone). `testing_parametrize` stays
  robust but is no longer the runaway #1 it was in v1 (was +5.44, now +2.2-2.6).

## 4. Honest caveats (for both papers)

- **Variance components are prior-sensitive** (psense on M4: σ_model lik-sens 0.33, σ_tmodel
  0.37, σ_alpha 0.14; μ fixed effects fine). Intrinsic — few groups (5 models, 3 codebases),
  not a fixable prior bug. Report rankings (stable) over σ magnitudes (wobble).
- **Measurement triangulation is weak:** checker↔judge quadratic-weighted κ panel-median ≈ 0.13
  (v1-5 judge logs; judge_1 0.13, judge_2 0.03, judge_3 0.17). Low agreement concentrates on
  judgment-laden style/docs decisions; robust effects sit on syntactically unambiguous checkers.
- **Pool-dependence** of the variance components (§1) — must be reported as a sensitivity, not
  hidden.
- **Context length is non-uniform** (bambi ~85K, arviz ~149K, pymc ~187K median peak), contra
  the paper's "~200K uniform"; but codebase variance is small (σ_codebase 0.25-0.36) and adding
  a per-codebase treatment slope (M5 in v5 docs) was null.
- **The BKT reinforcement loop (`tracker.py`) was never wired into the eval.** Selective
  reinforcement is motivation, not a run result. Do not overclaim a closed-loop policy.
- Framing arms exist for only 3 models (qwen, gemini, gpt-5.4-nano) — R3's negation test is not
  full-factorial.

## 5. The eval-methodology white space (study B)

From the literature sweep (2026-06-25). Field consensus: **binary 2PL IRT via variational
inference** (py-irt/Pyro) — Lalor (EMNLP 2016, arXiv:1605.08889; 2018; 2019; DDaCLAE 2020),
Rodriguez et al. (ACL 2021, leaderboards), Vania et al. (ACL 2021, 2106.00840), tinyBenchmarks
(Polo, ICML 2024, 2402.14992), metabench (ICLR 2025, 2407.12844), Lost-in-Benchmarks (AAAI 2026,
2505.15055). Use-case has shifted to efficient benchmarking / item subselection.

Adjacent rigour: error bars (Miller, Anthropic 2024, 2411.00640; Bowyer 2025 no-CLT-small-n,
2503.01747), construct validity (Freiesleben & Zezulka 2025 2510.23191; Bean et al. 2025
2511.04703), generalizability theory in LLM eval (Song 2025 2507.19980), ranking with
uncertainty (Chatbot Arena BT, Chiang 2024 2403.04132; PPI Boyeau 2024 2403.07008),
LLM-as-judge reliability (Zheng 2023 2306.05685 + κ-over-raw-agreement critiques).

Method foundations: Samejima 1969 (GRM), De Boeck & Wilson 2004 (explanatory IRT / LLTM),
Baayen 2008 (crossed REs), Cronbach 1972 / Brennan 2001 (G-theory), Bürkner 2021 (Bayesian IRT
in brms, 1905.09501), McElreath 2020 (ordered logit), LKJ 2009, Betancourt (induced-Dirichlet
cutpoints), Gelman 2006 (variance priors).

**Three gaps nobody occupies (mid-2026):** (1) responses treated as **ordinal/graded** not
binarized — only Choi et al. 2026 (2602.00521) uses a GRM, and only for judge-reliability, not
systems-under-test; (2) explanatory IRT with a covariate as an **experimental treatment on
ability** — never done (explanatory IRT only decomposes item *difficulty*: General Scales 2025
2503.06378, AutoIRT 2024 2409.08823); (3) **full hierarchical Bayesian (MCMC)** with crossed
model×item effects + partial pooling — most "Bayesian" eval work is variational for scale.

**The contribution:** a hierarchical Bayesian graded-response model with crossed model×item
effects, a **model×item interaction variance component**, and **treatment covariates on ability**,
fit by MCMC, for evaluating the systems under test. M8 instantiates it. The retention study is
the case study where it changes the conclusions (the interaction dominates; the v1 additive
model + raw means mischaracterize the phenomenon and manufacture a spurious "backfire").

## 6. Two-paper plan

- **A — Extended retention paper (journal).** M8 canonical. Thesis: instruction retention is a
  (model × instruction) interaction; the v1 "backfire" is a measurement artifact; heterogeneity
  is real but additive model main effects are negligible. AIS framing: deployed agents in loops
  with no oversight; safety doesn't transfer across context length. Reuses the camera-ready
  intro/method; new Results (M8), framing section (R3, null), measurement-validity section (κ),
  model-set sensitivity.
- **B — Eval-methodology paper.** "Hierarchical Bayesian graded-response models with a
  model×item interaction should be the standard for eval analysis." Positioned in the 3-gap
  white space; the model ladder (this note, §2) is the evidence; retention is the case study.

## 7. Artifacts

`analysis-out-v1/` (clean v1-5): `retention_v2.nc` (M4), `retention_v2_framing.nc`,
`retention_v2_M8_interaction.nc`, `ladder_{M0,M4,M8,M_irt,M_corr}.nc`, `treatment_ranking.csv`,
`variance_components.csv`, `model_treatment_slopes.csv`, `framing_effect.csv`, `scores.csv`.
`analysis-out-cand6/`, `analysis-out/` (10-model) for the sensitivity. Scratch fit scripts:
`scratchpad/{advanced,models2,m0_vs_m4}.py`. κ over judge logs: `analysis-out-kappa/`.
