# Repository materials

This repo holds both the **v2 benchmark code** (Inspect AI port — see `README.md`)
and the **paper + supporting materials** consolidated here from the old
`datascience-2026/` working folder. Map:

| Directory | Contents |
|-----------|----------|
| `src/`, `run.py`, `run_framing.py`, `analyze.py`, `models.toml` | **v2** benchmark (the active code; documented in `README.md`). |
| `paper/` | The JAIIO/ASAID 2026 paper — `paper.tex`, `references.bib`, `figures/`, compiled `paper.pdf` (and submission PDF). Built with LLNCS; the abstract is EN then ES. Current numbers are **v1**; v2 numbers are not yet frozen. |
| `experiments-v1/` | The frozen v1 one-off harness + the final v1 Bayesian results and figures the paper currently cites. See `experiments-v1/README.md`. |
| `docs/plans/` | Project planning. Most relevant: `2026-06-04-jaiio-camera-ready-y-futuro-trabajo.md` — the camera-ready (text-only, due 2026-06-29) + phase-2 (Azure $5k) roadmap and reviewer responses (R1/R2/R3). |
| `presentation/` | Talk materials — `guion*.md` (speaker scripts), `presentacion-*.tex` (Beamer slides), `Korenblit_*.pdf/pptx` (deliverables), `one-pager.{tex,pdf}`, `experiment-design.{tex,pdf}`, `img/` (interpretability figures). |
| `course/` | Ciencia de Datos 1C2026 final-work deliverables — `trabajo-final.{tex,docx}`, compiled `Korenblit-CdD-1C2026-trabajo-final.pdf`, `borrador-trabajo-final-v1.md` (Spanish draft), submission guide, `ovi-2.pdf`. |
| `tools/pdf2pptx/` | Utility used to convert slide PDFs to PPTX. |

## v1 vs v2 at a glance

v1 (`experiments-v1/`) is the published study: a bespoke Python runner, qwen judging
qwen, compliance measured at turns 20–25, 244 observations. v2 (repo root) re-runs the
same design on Inspect AI with epochs, a cross-family judge panel (no self-grading),
a deterministic+judge dual scorer, and a negation-framing arm — the version for the
extended/camera-ready numbers.

## Build the paper

    cd paper && pdflatex paper && biber paper && pdflatex paper && pdflatex paper

## Build a slide deck

    cd presentation && xelatex presentacion-instancia2.tex   # Beamer, needs XeLaTeX (fontspec)
