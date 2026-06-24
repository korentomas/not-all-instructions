# Bayesian model exploration — v5-rescored data (2026-06-24)

Exploring the v2 retention model: is the current spec sound, and can a simple
alternative catch effects better? **This is v2/continuation work — the accepted
(camera-ready) paper is frozen and uses the v1 model.** Data: `logs/rescored-v5`,
main fit = baseline+treatment = 1,967 obs across 10 models, 3 codebases, 12 decisions.

Script: `scratchpad/bayes_explore.py` (+ `bayes_explore2.py` for the M1-based round).
Constraint from the user: keep models simple — at most ~1 order of magnitude more
complex than the current model.

## Models (round 1)

| ID | Spec | vs current |
|----|------|-----------|
| **M0** | current: per-decision α, β (ordered-logit, offset cutpoints), pooled over model/codebase | baseline |
| **M1** | M0 + per-model + per-codebase **intercepts** (non-centered) | +~15 params |
| **M3** | M0 with heavy-tailed (StudentT ν=3) per-decision effects | same size |

(M2 — per-conversation random intercepts, ~300 levels — was dropped as too complex.)

## Round 1 results

**LOO comparison:**

| Model | ELPD | ΔELPD | note |
|-------|------|-------|------|
| M3 | −1136.1 | 0 | tied with M1; 2 divergences |
| M1 | −1136.6 | −0.5 ± 0.35 | tied (indistinguishable from M3) |
| M0 | −1247.1 | **−111 ± 15** | decisively worst |

**The current model (M0) is misspecified.** Adding per-model + per-codebase intercepts
improves ELPD by ~111 (±15) — a decisive gap. M3's heavy tails add nothing over M1
(Δ0.5) and introduce divergences, so M1 is preferred (simpler, cleaner).

**Headline: model identity explains as much variance as instruction type.**

| Variance component | M1 estimate (94% HDI) |
|--------------------|----------------------|
| σ_β (instruction type) | 1.14 [0.59, 1.73] |
| **σ_model** | **1.08 [0.61, 1.63]** |
| σ_codebase | 0.36 [0.0, 0.92] |

This **overturns the accepted paper's finding #3** ("neither model architecture nor
codebase size explains meaningful variance"). That v1 claim was an artifact of the
baseline condition coming from Qwen only; with v2's full baselines across 10 models,
**which model you run matters as much as which instruction.** Codebase still matters
little.

**Effects are more honest, not more numerous.** Effective decisions (94% HDI excludes 0):
M0 = 8, **M1 = 6**. M0 over-counted — `testing_assert_almost` and `naming_snake_no_abbrev`
lose significance once per-model variance is absorbed (their apparent effect was partly
model confounding). The 6 robust winners (M1):

| decision | β (M1) | 94% HDI |
|----------|--------|---------|
| testing_parametrize | +2.95 | [2.15, 3.83] |
| dependencies_module_constants | +2.84 | [1.58, 4.12] |
| docs_regex_comments | +1.73 | [0.79, 2.66] |
| naming_underscore | +1.31 | [0.72, 1.93] |
| docs_numpy_style | +0.98 | [0.23, 1.74] |
| architecture_standalone | +0.86 | [0.27, 1.47] |

`dependencies_no_new` ≈ 0 in every spec (M0 +0.06, M1 −0.04) — the v1 "backfire" stays
dead and robust. σ_β ≈ 1.0–1.1 throughout, so the core heterogeneity thesis holds (about
half the v1 magnitude of 2.11).

**Diagnostics:** all converged. R̂ ≤ 1.003, min ESS > 1400. Divergences M0=0, M1=1, M3=2.
M1's single divergence clears with `target_accept=0.99`.

## Recommendation (round 1)

Adopt **M1** (current + per-model + per-codebase intercepts) as the v2 base model. One
step more complex, decisively better fit, clean, and it surfaces the model-identity
effect. Skip M3.

## Round 2 — M1-based extensions (in progress)

Building on M1, three simple extensions (each ~one step beyond M1):

| ID | Spec | Question |
|----|------|----------|
| **M4** | M1 + per-model **treatment slope** | Do models differ in *how much* they retain when told, not just baseline? |
| **M5** | M1 + per-codebase **treatment slope** | Does context pressure (codebase size) modulate retention? (the context-rot question) |
| **M6** | M1 + decision **category level** (nested) | Is the heterogeneity at the category level or the specific-instruction level? |

### Round 2 results

All three fit cleanly (0 divergences at `target_accept=0.99`, R̂ ≤ 1.004, ESS > 1400).

**LOO comparison:**

| Model | ELPD | ΔELPD vs M4 | verdict |
|-------|------|-------------|---------|
| **M4** (M1 + per-model treatment slope) | −1128.1 | 0 | **best** |
| M1 (base) | −1136.6 | −8.5 ± 4.7 | |
| M6 (+category level) | −1137.3 | −9.3 | no gain over M1 |
| M5 (+codebase treatment slope) | −1137.5 | −9.4 | no gain over M1 |

**M4 — models differ in responsiveness, not just baseline.** σ_tmodel = 0.82 [0.35, 1.34]
(excludes 0). Per-model treatment slopes: **qwen3.5-27b (+0.97 [0.15, 1.77]) and
qwen3.5-plus (+0.89 [0.11, 1.73]) are the only two with HDI above zero** — Qwen models
retain instructions when told *more than the others do*. Since **Qwen was the v1 paper's
primary model**, the v1 headline treatment effects are partly Qwen-specific. M4 improves on
M1 by ΔLOO +8.5 ± 4.7 (moderate, ~1.8 SE).

**M5 — context pressure does NOT modulate retention.** σ_tcodebase = 0.32 [0.0, 0.93]
(includes 0); no LOO gain. Codebase size does not change how strongly an instruction is
retained.

**M6 — heterogeneity is instruction-specific, not type/category.** σ_cat = 0.39 [0.0, 1.01]
(includes 0); no LOO gain. Confirms the earlier hand-aggregation (within-category variance
dominates between-category): the *category/type* does not carry the effect on coding data.

### Variance components (M4, the best model)

| component | estimate (94% HDI) | matters? |
|-----------|--------------------|----------|
| σ_β (instruction type) | ~1.0 [0.52, 1.59] | yes |
| σ_model (baseline level) | ~0.9 [0.47, 1.43] | yes |
| σ_tmodel (treatment responsiveness) | 0.82 [0.35, 1.34] | **yes — new effect M0/M1 missed** |
| σ_codebase | ~0.37 [0.0, 0.92] | weak |
| σ_tcodebase (codebase × treatment) | 0.32 [0.0, 0.93] | no |
| σ_cat (category/type) | 0.39 [0.0, 1.01] | no |

M4 effective decisions (HDI excludes 0): 5 — parametrize, module_constants, regex_comments,
numpy_style, underscore (architecture_standalone drops to borderline).

## Final recommendation

Use **M4** as the v2 base model: current per-decision α/β ordered-logit **+ per-model and
per-codebase intercepts + per-model treatment slope** (`target_accept=0.99`). ~55 params,
still within ~1 order of magnitude of the original. It fits decisively better than the
current model (ΔLOO ≈ 119 vs M0) and surfaces effects the flat model cannot see.

**Takeaways for the continuation (not the frozen camera-ready):**
1. Model identity matters at *both* the baseline (σ_model ≈ 0.9) and the treatment-response
   (σ_tmodel ≈ 0.82) level — the v1 "model doesn't matter" claim is doubly wrong once
   baselines exist for all models.
2. Qwen (the v1 primary model) is the most instruction-responsive; v1's headline effects
   are partly Qwen-specific.
3. Retention heterogeneity is **instruction-specific**, not explained by category/type (M6)
   or by context pressure / codebase (M5).
4. The `dependencies_no_new` "backfire" is ≈0 in every specification — a non-replicated v1
   artifact.

Artifacts: traces + CSVs in the run's scratch `bayes_out/` (`M{0,1,3,4,5,6}.nc`,
`beta_*.csv`, `loo_compare*.csv`, `summary*.json`); scripts `scratchpad/bayes_explore.py`
and `bayes_explore2.py`. To promote M4 into the codebase, fold the per-model/codebase
intercepts + per-model treatment slope into `src/retention/analysis/model.py`.

## M4 validation (criticism pass)

Full criticism of M4 — all clean except a tooling note:

| Check | Result |
|-------|--------|
| Convergence | 0 divergences, R̂max 1.005, min ESS 1341 ✓ |
| Prior predictive | scores span 0–3, non-degenerate ✓ |
| PPC category calibration | obs vs pred near-exact, all 4 categories inside 94% ✓ |
| PPC per-decision | all 12 decision means inside 94% ✓ |
| LOO reliability | Pareto k_max 0.40, 0 of n with k>0.7 ✓ |

Data note: scores are effectively **bimodal** — 0 (33%) and 3 (61%); scores 1–2 are rare
(~5%, ~1%). The checkers mostly fire "violated" or "fully followed"; the ordinal is
near-binary in practice, so the middle cutpoints are weakly informed. The model reproduces
this distribution almost exactly.

## Prior sensitivity (psense, power-scaling — Kallioinen et al. 2024)

`arviz_stats.psense_summary` (needed `pip install arviz-base`). On M4:

| param | prior sens | likelihood sens | flag |
|-------|-----------|-----------------|------|
| σ_model | 0.28 | 0.05 | prior-data conflict |
| σ_alpha | 0.26 | 0.08 | prior-data conflict |
| σ_beta | 0.20 | 0.14 | prior-data conflict |
| σ_tmodel | 0.17 | 0.07 | prior-data conflict |
| σ_codebase | 0.075 | 0.08 | borderline |
| μ_beta, μ_alpha | 0.074 | low | mild strong-prior |

(threshold 0.05.) The **variance components are prior-sensitive**; fixed effects (μ) are
essentially fine.

## Round 3 — can we beat M4? (driven by the psense finding)

| ID | Spec | Result |
|----|------|--------|
| **M4b** | M4 with relaxed `HalfNormal(2.5)` σ priors | ΔLOO +0.18 vs M4 (no improvement); σ's grow slightly (σ_β 1.12, σ_model 1.00, σ_codebase 0.51) but **psense still flags them** (σ_alpha 0.34) |
| **M7** | M4 + rank-1 model×decision treatment interaction (factor model) | ELPD looks 50 better **but DID NOT CONVERGE** (R̂ 1.74, ESS 6) — classic factor-model sign/scale unidentifiability. **Invalid as-is.** |

**Two conclusions:**
1. The σ prior-sensitivity is **intrinsic, not a fixable prior bug.** With only 3 codebases /
   10 models / 12 decisions, the variance components are weakly identified — widening the
   prior (M4b) doesn't resolve the conflict and doesn't improve fit. Report σ estimates with
   this caveat; the *rankings* are stable, only the σ magnitudes wobble with the prior.
2. The naive rank-1 factor model (M7) is **unidentified** — its LOO "win" is a
   non-convergence artifact. A properly-identified version (positive/ordered loadings) could
   be revisited, but it exceeds the "keep it simple" bar.

## Final model decision

**M4** = current ordered-logit + per-model & per-codebase intercepts + per-model treatment
slope. Best-fitting identifiable model, fully validated (calibration + PPC + LOO clean).
Caveat to disclose: variance-component (σ) estimates are prior-influenced due to few groups;
scientific conclusions (effective-decision ranking, model-identity matters, dead backfire,
σ_β ≈ 1) are robust across every specification tried.

Artifacts added: `M4_validated.nc`, `M4b.nc`, `M7.nc`, `m4_validation.json`, `summary3.json`,
`loo_compare3.csv` in the run scratch `bayes_out/`; scripts `validate_m4.py`, `find_better.py`.

## Non-Bayesian cross-check (gradient-boosted trees + feature selection)

A learning probe (not for the paper): engineered 15 features (treatment, decision, category,
model, family, vendor, size_b, codebase, measured context_k, lines_k, is_negation,
plant_turn, test_turn, decay-distance, timing, epoch) and predicted the 0–3 score with
gradient-boosted trees, grouped CV by conversation. Script: `scratchpad/feature_ml.py`.

**Model comparison (GroupKFold-5, R²):** RandomForest 0.609 ± 0.05, HistGBM 0.603 ± 0.07,
Ridge (linear) 0.148. Trees ≈ 0.6; linear collapses → the structure is
nonlinear/interaction-driven, which justifies the hierarchical model.

**Permutation importance:** decision +1.00 ≫ family +0.21 > treatment +0.15 ≈ model +0.15 >
codebase +0.08 ≫ (epoch +0.02, test_turn +0.015, everything else ≈ 0: timing, is_negation,
category, context_k, lines_k, **decay-distance**, size_b, plant_turn).

**Agreement with the Bayesian model (independent method, same story):**
- Same variance ordering: decision ≫ model/family > treatment > codebase (weak).
- category ≈ 0 → instruction-specific, not type (confirms M6).
- decay-distance ≈ 0, timing ≈ 0 → no turn-distance decay in the 20–25 window.
- context_k = lines_k = size_b = 0 → it's model/codebase *identity*, not context size or
  parameter count (confirms M5 null).
- is_negation ≈ 0 → negation framing doesn't predict (matches dead backfire / framing-null).

**Feature selection re-derives M4:** the predictive set is exactly {decision, model/family,
treatment, codebase} — the same terms M4 uses. An orthogonal method independently lands on
M4's structure. epoch (a replicate id) sits at ~0, a clean negative control.

## Interaction discovery (Friedman's H on the tree)

To check whether the model×decision interaction M7 tried (and failed, unidentified) to
capture is real, computed Friedman's H per feature pair on the gradient-boosted tree
(`scratchpad/interaction_h.py`):

| pair | H (0 = additive, →1 strong) |
|------|------------------------------|
| **model × decision** | **0.52** |
| treatment × decision | 0.25 (= β_d heterogeneity) |
| treatment × model | 0.25 (= M4's per-model slope) |
| codebase × decision | 0.21 |
| treatment × codebase | 0.13 |

**model×decision is the strongest interaction (H=0.52)** — which instruction a model retains
depends on the specific model×instruction pairing, beyond additive effects. So M7's signal
was *real*; only its naive rank-1 parameterization was unidentified. **Future enhancement:**
an identifiable factor model (positive/ordered loadings) for the model×decision interaction.
M4 (additive) stays the simple base for now.

## M4 promoted into the codebase (2026-06-24)

M4 is now the production model, not just an exploration artifact:
- `src/retention/analysis/model.py::fit_ordered_logit` — adds per-model & per-codebase
  intercepts + per-model treatment slope when those columns have >1 level (graceful: reduces
  to the per-decision spec otherwise). `target_accept` default 0.95→0.99. New helpers
  `variance_components()` and `model_treatment_slopes()`.
- `analyze.py` — prints and writes `variance_components.csv` + `model_treatment_slopes.csv`.
- TDD: `tests/test_analysis.py::test_ordered_logit_adds_model_and_codebase_effects` (structure
  + per-model recovery + treatment split). Fast suite green; slow analysis tests green.
- End-to-end on `logs/rescored-v5`: σ_model 0.92, σ_tmodel 0.84, σ_codebase 0.36; qwen-27b
  (+0.98) and qwen-plus (+0.90) the only effective per-model slopes — Qwen most responsive.
- README + `pyproject` `[analysis]` extra updated (`arviz-base`, `arviz-stats`, `nutpie`).
