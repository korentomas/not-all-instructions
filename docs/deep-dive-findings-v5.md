# Deep dive — is the retention finding real? (2026-06-24)

An extended robustness pass on the v2 (rescored-v5) data, beyond the headline fit.
Scripts: `scratchpad/robustness_check.py`, `scratchpad/deep_dive.py`. v2 trace = `M4_validated.nc`.

## 1. Heterogeneity is real and robust
σ_β = 2.11 [1.14, 3.43] (v1), 1.03 [0.59, 1.68] (v2); P(σ_β > 0.5) ≈ 1.00 in both. Treatment
effects genuinely vary across instructions.

## 2. …and not just the baseline ceiling
Regressing per-decision β on baseline α: **R² = 0.44** — baseline headroom explains 44% of
the cross-instruction β spread, but **56% of the variance is instruction-specific** (residual
SD 0.60 of total 0.83). So "not all instructions forgotten equal" survives adjusting for
how much room each instruction had to improve.

## 3. But it's a model×instruction interaction, not instruction-alone
- **Cross-model concordance is weak:** Kendall's W = 0.27 (χ² p = 0.001), mean pairwise
  Spearman of per-decision lift = +0.26. Models only weakly agree on *which* instructions
  respond to being told.
- Friedman's H(model × decision) = 0.52 on the gradient-boosted tree (strongest pair).
- σ_tmodel = 0.83 [0.36, 1.34] — models differ in overall responsiveness.

→ **This contradicts the published finding #3** ("the variation is almost entirely in the
instruction type itself, not the model"). The honest statement: retention is a property of
the **(model, instruction) pair**. The interaction is as large as the main effects.

## 4. One robust universal effect; the rest is model-dependent or null
Sign agreement across the 10 v2 models (fraction with positive treatment lift):

| decision | mean lift | models positive | verdict |
|----------|-----------|-----------------|---------|
| testing_parametrize | +1.34 | 80% | **consistent winner** |
| naming_underscore | +0.66 | 80% | consistent |
| docs_numpy_style | +0.33 | 70% | leans positive |
| dependencies_module_constants | +0.59 | 60% | mixed |
| docs_regex_comments | +0.86 | 50% | mixed |
| architecture_standalone | +0.50 | 50% | mixed |
| code_style_listcomp | +0.50 | 10% | inconsistent |
| naming_snake_no_abbrev / broadcasting / assert_almost / arch_extend | ~0 | 0–40% | null |
| dependencies_no_new | −0.10 | 10% | null (v1 "harm" is dead) |

`testing_parametrize` is the one effect with P(β>0)=1.00 in **both** v1 and v2 *and* 80%
cross-model sign agreement: models almost never parametrize tests by default but reliably do
when asked. That is the cleanest, most defensible single finding.

## 5. Planting position has no effect
Early-planted (turns 1–7) mean lift +0.37; late-planted (turns 14–19) +0.36 — identical.
Retention here is not driven by recency/position of the request. (Consistent with the ML
probe: decay-distance importance ≈ 0.)

## 6. The "harm" finding does not hold
`dependencies_no_new`: v1 β=−2.36 but 94% HDI upper = −0.03 (clears zero by a hair; P(β<0)=0.98,
fails at ~96%). v2 β=−0.14, P(β<0)=0.63 — dead. Cross-model: 10% positive (consistently null,
not consistently harmful). It is a v1 checker artifact (re-shown imports), not a real harm.

## What to claim (defensible)
1. Stating an instruction reliably helps a **subset** the model won't do by default — led by
   `testing_parametrize`, with a couple of moderate others.
2. Per-instruction treatment heterogeneity is **real and not just baseline headroom**.
3. Retention is **model-dependent**: a (model, instruction) interaction, not instruction-alone.

## What to drop
- "One instruction actively harmed by reinforcement" (fragile in v1, dead in v2).
- "Neither model nor codebase explains the variance" (model identity matters; weak concordance).

## 7. Robustness battery (jackknife + binary)

Frequentist jackknife on per-decision treatment lift (`scratchpad/leave_one_out.py`):

- **Leave-one-model-out (all 10):** `testing_parametrize` lift stays +1.15…+1.51;
  heterogeneity SD 0.39…0.49 (full 0.44). No single model drives it.
- **Leave-one-codebase-out (all 3):** parametrize +1.18…+1.47; heterogeneity SD 0.44…0.88
  (jumps when arviz is dropped — codebase-sensitive magnitude, but always nonzero; only 3
  codebases so the jackknife is volatile).
- **Binary collapse (compliant = score ≥ 2):** parametrize is rank #1 of 12 (+0.45); same top
  set (regex_comments, module_constants, underscore). The finding is not an ordinal-scale artifact.

`testing_parametrize` survives every robustness cut (model, codebase, binary, v1, v2) — it is
the one bulletproof effect. Heterogeneity is robust to model removal and to binarization.

## Verdict

Yes, there is a real finding, robust under stress: **stating an instruction reliably helps a
specific subset the model won't do by default (led by `testing_parametrize`), the
per-instruction heterogeneity is genuine and not just baseline headroom, and retention is a
(model, instruction) interaction rather than an instruction-only property.** The published
"one instruction harmed" and "model doesn't matter" framings do not survive; the core does.

## 8. Power: which "nulls" are real nulls?

Classifying the non-effective decisions by precision (v2 trace; P(|β|<0.5) and HDI width):

- **5 effective:** parametrize, module_constants, regex_comments, numpy_style, underscore.
- **2 confirmed precise-null:** `code_style_broadcasting` (β+0.12, P(|β|<0.5)=0.68) and
  `dependencies_no_new` (β−0.14, P=0.77) — genuinely ≈0, well-estimated. The backfire is a
  *confirmed* null, not merely uncertain.
- **5 underpowered:** listcomp (HDI width 4.0), snake, assert_almost, arch_extend,
  arch_standalone — wide intervals, undetermined; these need more data.

So "8 need no intervention" is really 2 confirmed-no-effect + ~3 borderline + 5 undetermined.

## 9. Measurement validity — checker vs LLM judge (κ)

Quadratic-weighted checker↔judge agreement on the original v2 logs (4298 deterministic obs,
3-judge cross-family panel): judge_1 0.21, judge_2 0.10, judge_3 0.28, **panel median 0.21**.
Low (slight–fair). The deterministic checker and independent judgment only weakly agree, and
the judges disagree among themselves.

Reading: the low κ concentrates on **judgment-laden decisions** (style, docs) where
"compliance" is genuinely fuzzy; the **robust effects sit on syntactically unambiguous
checkers** (`testing_parametrize` = is `@pytest.mark.parametrize` present), which need no
judgment and survive binarization — so validity is not at stake for the headline, only for
the uncertain/underpowered decisions already flagged. Caveat: computed on the v4 (pre-fix)
deterministic scores; v5 would shift it. Still, it argues for the triangulated
checker+judge measurement listed in the paper's future work.

Figures: `report-figures/fig5_lift_heatmap.png` (model × instruction lift). Scripts:
`scratchpad/{robustness_check,deep_dive,leave_one_out}.py`.
