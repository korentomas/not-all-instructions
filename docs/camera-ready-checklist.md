# Camera-ready checklist — "Not All Instructions Are Forgotten Equal" (JAIIO/ASAID 2026)

**Deadline: 2026-06-29.** Principle: **text-only, v1 numbers — NO new epochs, no M4, no v2 data.**
(The v2 runs / M4 / corrected story are the *extended paper*, a separate output.)

Reviewer asks (R1 broader baselines, R3 negation paraphrase) are *suggestions on an accepted
paper* — addressed in text via Future Work, not by running experiments. No second review round.

Files: `paper/paper.tex` (working camera-ready), `paper/paper_camera_ready_v1.tex` (frozen
snapshot), `paper/Not_All_..._JAIIO_2026.pdf` (the accepted submission, untouched).

---

## DONE — text edits already applied to `paper.tex`

- [x] **ESS fix** — ">1400" → "= 1311" (×2: §Bayesian model, §Results); R̂ ≤ 1.01 wording accurate.
- [x] **Finding #2 hedged** — "actively harmed by reinforcement" → "a marginal negative effect"
      everywhere (abstract EN+ES, intro finding list, §4.2 header + body, §Reinforcement
      priorities prose, Conclusion). §4.2 adds the honest caveat: 94% HDI barely excludes zero
      + the `no_new_imports` checker counts re-shown imports → "candidate measurement artifact,
      not a robust harm." Table 2 action `Never reinforce` → `Avoid (marginal)`.
- [x] **Finding #3 softened** — "neither model nor codebase explains meaningful variance" →
      "we find little evidence that…"; §Model-and-codebase adds the single-model-baseline caveat.
- [x] **Dataset clarification** — "not every conversation produced a scorable response at every
      test turn" (28 runs launched vs 244 contributing observations).
- [x] **Table 2 count fix** — "6 other types" → "5 other types" (table now sums to 12).
- [x] **Abstract overclaim** — "retained perfectly when stated" → "retained when stated" (EN+ES).
- [x] **σ_β wording** — "respond very differently" → "respond differently."
- [x] **Laban citation** — "compliance drops of up to 39%" → "average compliance drops of 39%"
      (intro now matches Related work + Laban's actual result).
- [x] **R1/R3 reviewer responses** — Future Work expanded to 6 directions explicitly naming
      full-factorial baselines across all models (R1) and negated/positive paraphrase test (R3);
      Discussion sentence credits R3's design.
- [x] **Register pass** — PowerBench register tightening (no inflation, measured tone).
- [x] **Full proofread** — every section read; numbers cross-checked against artifacts.
- [x] **Anonymization** — `\author{}` / `\institute{}` blank (JAIIO anonymized submission).
- [x] **Reviews archived** — `docs/reviews-jaiio-249.md`.

## LEFT — still text/reproducibility only (no new epochs)

- [x] **1. Full-model claim** (DONE). Refit the full model (per-model + per-codebase
      intercepts) on the reconstructed v1 data (`experiments-v1/analysis/refit_full_model.py`,
      trace archived to `retention_full_model.nc`): it gave **0 divergences** (not 267 — that
      number does not reproduce; a clean non-centered fit converges) with σ_model and
      σ_codebase ≈ 0.3, 94% intervals spanning zero. So the paper now **drops the "267
      divergent transitions"** (over-precise, unreproducible) and justifies dropping the terms
      by their **near-zero variance** instead (both §Bayesian model and §Model-and-codebase),
      noting per-model effects are weakly identified with a single-model baseline. No new epochs.
- [x] **2. De-anonymization** (DONE, JAIIO requires it for camera-ready). Added author block:
      Tom\'as P. Korenblit, ORCID 0009-0002-5682-8475, Universidad Nacional de San Mart\'in,
      `tomaskorenblit@gmail.com`; `\titlerunning`/`\authorrunning`; fixed "authors"→"author"
      (single author); copied `ORCID-iD_icon_16x16.png` from the template.
      **VERIFY:** name spelling, exact affiliation string, email, ORCID.
- [x] **3. LLM-usage statement** (DONE) — `\subsubsection{Use of large language models}` in
      credits (Claude assisted drafting/revising + analysis/figure code; results computed by
      checkers + statistical models and verified by the author). **VERIFY** wording against the
      JAIIO/CMT "provided template" (the page says "adapted from the provided template").
- [x] **Format/compliance** — LNCS ✓; **14 pages (= the 14-page max for full articles)** ✓;
      references render APA 7 (biber ✓, 26 entries); EN+ES keywords ✓; EN title/abstract → ES
      → body ✓; all 4 figures present ✓; **0 overfull, 0 unresolved refs**.
- [ ] **4. Final build + submit** — compile final PDF, upload via **CMT**
      (https://cmt3.research.microsoft.com/55JAIIO2026) before the camera-ready deadline.
      *(Author action.)* Submission system = CMT; full article ≤ 14 pp.
- [ ] **5. Commit** — all camera-ready edits + this checklist + frozen snapshot
      (`paper/paper_camera_ready_v1.tex`) currently uncommitted on `v2-analysis-and-camera-ready`.

## Reference: JAIIO/ASAID rules (from tipos-trabajo + template)
- Full article **≤ 14 pages**; LNCS format (template: `JAIIO template overleaf/`).
- English article ⇒ English title+abstract, then **Spanish title+abstract+keywords** (✓).
- Camera-ready **de-anonymized**: every author's name, ORCID, institution, email (✓).
- **LLM-usage statement required** if LLMs used (✓).
- References: **APA 7** (guide: `Documento_completo.pdf`); paper uses biblatex `apa` (✓).
- Submit via **CMT**.

## Explicitly NOT in the camera-ready
- No new epochs, models, or runs.
- No M4 / per-model effects (that reverses finding #3 — extended paper only).
- No v2 figures (the v1 figures stay).
- No re-scored / abstain-contract numbers (v2 only).

## Build commands
```
cd paper && pdflatex paper && biber paper && pdflatex paper && pdflatex paper
```
