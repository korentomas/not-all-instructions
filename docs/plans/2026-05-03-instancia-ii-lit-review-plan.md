# Instancia II Lit Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 7-slide, 5-minute Beamer presentation for Instancia II (literature review on Context Rot in LLMs), and ship it as a `.pptx` file by 2026-05-07.

**Architecture:** Single `presentacion-instancia2.tex` file (Beamer + metropolis, light theme), compiled with xelatex, then converted to image-PPT via the `ashafaei/pdf2pptx` tool. A `Makefile` target orchestrates the build.

**Tech Stack:** LaTeX (xelatex), Beamer, metropolis theme, booktabs, pgfplots, `pdf2pptx`.

**Working dir:** `/Users/tk/Documents/Personal/Lab/datascience-2026/`

**User reminder:** the user wants to learn — review prose in each slide and adjust to your voice (Argentine Spanish, voseo, conversational). This plan provides scaffolding, not your final words.

---

## File Structure

| File | Status | Responsibility |
|---|---|---|
| `presentacion-instancia2.tex` | Create | The 7 slides + references appendix |
| `Makefile` | Create | Build targets: `pdf`, `pptx`, `clean` |
| `tools/pdf2pptx/` | Clone | Conversion tool (gitignored) |
| `.gitignore` | Modify | Ignore `tools/`, build artifacts of new file |

---

## Task 0: Infrastructure setup

**Files:**
- Create: `.gitignore` entries
- Create: `tools/pdf2pptx/` (cloned)

- [ ] **Step 1: Check current `.gitignore`**

```bash
cat .gitignore 2>/dev/null || echo "no gitignore"
```

If file does not exist, create it. If it exists, you'll append.

- [ ] **Step 2: Add ignore entries**

Append to `.gitignore` (create if missing):

```
# Build tools
tools/

# Build artifacts for instancia2
presentacion-instancia2.aux
presentacion-instancia2.log
presentacion-instancia2.nav
presentacion-instancia2.out
presentacion-instancia2.snm
presentacion-instancia2.toc
presentacion-instancia2.pdf
presentacion-instancia2.pdf.pptx
```

- [ ] **Step 3: Clone pdf2pptx**

```bash
mkdir -p tools
git clone https://github.com/ashafaei/pdf2pptx.git tools/pdf2pptx
```

Expected: clone succeeds, directory has `pdf2pptx.sh` inside.

- [ ] **Step 4: Install pdf2pptx dependencies**

```bash
pip install -r tools/pdf2pptx/requirements.txt
```

Expected: `python-pptx` and `pdf2image` install (or already satisfied).

- [ ] **Step 5: Verify pdf2pptx runs**

```bash
ls tools/pdf2pptx/pdf2pptx.sh
bash tools/pdf2pptx/pdf2pptx.sh 2>&1 | head -5
```

Expected: usage/help text. Confirms tool is callable.

- [ ] **Step 6: Commit**

```bash
git add .gitignore
git commit -m "chore: ignore instancia2 build artifacts and pdf2pptx tool"
```

---

## Task 1: LaTeX skeleton

**Files:**
- Create: `presentacion-instancia2.tex`

- [ ] **Step 1: Write the skeleton**

Create `presentacion-instancia2.tex` with this content:

```latex
% !TEX program = xelatex
\documentclass[aspectratio=169, 11pt]{beamer}

\usetheme{metropolis}
\usepackage{appendixnumberbeamer}
\usepackage{booktabs}
\usepackage{amsmath, amssymb}
\usepackage{graphicx}
\usepackage{tikz}
\usetikzlibrary{arrows.meta, positioning}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}

% Light theme — single accent color, no dark overrides
\definecolor{accent}{HTML}{A43F2A}
\setbeamercolor{progress bar}{fg=accent}
\setbeamercolor{alerted text}{fg=accent}
\setbeamercolor{frametitle}{bg=white, fg=black}

\setbeamerfont{frametitle}{size=\normalsize, series=\bfseries}

\title{An\'alisis de soluciones existentes}
\subtitle{Context Rot en LLMs --- revisi\'on de literatura}
\author{Tom\'as Pablo Korenblit}
\date{Mayo 2026}
\institute{Licenciatura en Ciencia de Datos $\cdot$ Ciencia de Datos $\cdot$ 1C2026\\
Docentes: Rodrigo D\'iaz, Agust\'in Moro, Florencia Pi\~neyr\'ua}

\begin{document}

% Slides go here

\end{document}
```

- [ ] **Step 2: Compile and verify**

```bash
xelatex -interaction=nonstopmode presentacion-instancia2.tex
```

Expected: PDF generated with no slides (empty document is OK at this point — the `\begin{document}...\end{document}` block has no frames yet, so output may say "No pages of output" — that's expected).

If you want to confirm the preamble is valid before adding frames, add a temporary `\begin{frame}{Test}Test\end{frame}` between `\begin{document}` and `\end{document}`, recompile, then remove it.

- [ ] **Step 3: Commit**

```bash
git add presentacion-instancia2.tex
git commit -m "feat: instancia2 latex skeleton with light metropolis theme"
```

---

## Task 2: Slide 1 — Title

**Files:**
- Modify: `presentacion-instancia2.tex` (insert title frame after `\begin{document}`)

- [ ] **Step 1: Add the title frame**

Replace the comment `% Slides go here` with:

```latex
\maketitle
```

That's it. metropolis renders a clean title slide from the metadata you set in the preamble.

- [ ] **Step 2: Compile and view**

```bash
xelatex -interaction=nonstopmode presentacion-instancia2.tex
open presentacion-instancia2.pdf
```

Expected: 1 slide. Title, subtitle, your name, date, institution. Light background, no compass image.

- [ ] **Step 3: Review and adjust**

Look at the title. If you want to tweak wording (e.g. shorter subtitle), edit the `\title{}` and `\subtitle{}` in the preamble.

- [ ] **Step 4: Commit**

```bash
git add presentacion-instancia2.tex
git commit -m "feat: title slide for instancia2"
```

---

## Task 3: Slide 2 — Delimitación del problema

**Files:**
- Modify: `presentacion-instancia2.tex` (append after `\maketitle`)

- [ ] **Step 1: Add the frame**

Append after `\maketitle`:

```latex
\begin{frame}{Delimitaci\'on del problema}

\textbf{Context Rot:} los LLM pierden adherencia a las instrucciones a medida que la conversaci\'on crece.

\vspace{1em}

Lo introduje en Instancia I. Esta presentaci\'on revisa qu\'e dice la literatura sobre el problema.

\vspace{1.5em}

\textbf{Alcance de esta revisi\'on:}
\begin{itemize}
    \item Papers que \alert{miden} el fen\'omeno
    \item Papers que explican el \alert{mecanismo}
    \item Papers que proponen \alert{mitigaci\'on}
\end{itemize}

\end{frame}
```

- [ ] **Step 2: Compile and view**

```bash
xelatex -interaction=nonstopmode presentacion-instancia2.tex && open presentacion-instancia2.pdf
```

Expected: 2 slides. Slide 2 shows the bullets and one-liner.

- [ ] **Step 3: Review the prose**

Read the slide aloud. Does it sound like you? If not, rewrite. Common edits: shorter "Lo introduje en Instancia I" → "Ya lo present\'e en Instancia I."

- [ ] **Step 4: Commit**

```bash
git add presentacion-instancia2.tex
git commit -m "feat: slide 2 delimitacion"
```

---

## Task 4: Slide 3 — Eje 1: Medición del fenómeno

**Files:**
- Modify: `presentacion-instancia2.tex` (append)

- [ ] **Step 1: Add the frame**

```latex
\begin{frame}{Eje 1 --- Medici\'on del fen\'omeno}

\renewcommand{\arraystretch}{1.4}
\begin{table}
\centering
\footnotesize
\begin{tabular}{@{} p{4.5cm} p{3.5cm} p{3.5cm} @{}}
\toprule
\textbf{Estudio} & \textbf{Hallazgo} & \textbf{Setting} \\
\midrule
Laban et al.\ (2025) & \alert{39\%} de ca\'ida promedio & 15 modelos, multi-turn \\
He et al.\ (2024) -- Multi-IF & 87.7\% $\to$ \alert{70.7\%} & 3 turnos \\
Chroma Research (2025) & \alert{18/18} modelos afectados & Industria \\
\bottomrule
\end{tabular}
\end{table}

\vspace{0.8em}

\footnotesize
S\'intesis: los tres reportan m\'etricas \textbf{agregadas}. Ninguno desagrega por tipo de instrucci\'on.

\end{frame}
```

- [ ] **Step 2: Compile and view**

```bash
xelatex -interaction=nonstopmode presentacion-instancia2.tex && open presentacion-instancia2.pdf
```

Expected: slide 3 shows a clean 3-row table.

- [ ] **Step 3: Review**

The synthesis line is the most important — it's the seed of the gap you'll detect on slide 6. Make sure it's crisp.

- [ ] **Step 4: Commit**

```bash
git add presentacion-instancia2.tex
git commit -m "feat: slide 3 eje 1 medicion fenomeno"
```

---

## Task 5: Slide 4 — Eje 2: Mecanismo

**Files:**
- Modify: `presentacion-instancia2.tex` (append)

- [ ] **Step 1: Add the frame**

```latex
\begin{frame}{Eje 2 --- Mecanismo (¿por qu\'e pasa?)}

\begin{columns}[T]
\begin{column}{0.55\textwidth}
\textbf{Liu et al.\ (2024) --- Lost in the Middle}

\vspace{0.3em}
\footnotesize
La precisi\'on baja cuando la info est\'a en el medio del contexto. La atenci\'on no es uniforme.

\vspace{0.6em}

\begin{tikzpicture}
\begin{axis}[
    width=6cm, height=3.5cm,
    xlabel={Posici\'on}, ylabel={Accuracy (\%)},
    xmin=0, xmax=10, ymin=40, ymax=100,
    xtick={0, 5, 10}, xticklabels={Inicio, Medio, Final},
    ytick={50, 75, 100},
    grid=major, grid style={gray!20},
    axis lines=left, label style={font=\scriptsize},
    tick label style={font=\scriptsize},
]
\addplot[color=accent, ultra thick, smooth, tension=0.6]
    coordinates {(0,90) (1,85) (2,72) (3,58) (4,50) (5,48)
                 (6,50) (7,58) (8,72) (9,85) (10,92)};
\end{axis}
\end{tikzpicture}
\end{column}

\begin{column}{0.42\textwidth}
\textbf{Mu et al.\ (2025) --- Saturaci\'on}

\vspace{0.3em}
\footnotesize
Cuando el system prompt tiene m\'as de 50 reglas, la adherencia a cada una cae a $\sim$0\%.

\vspace{0.8em}

\textbf{Juntos:}
\vspace{0.3em}

\footnotesize
La atenci\'on no se reparte uniforme: ni por \alert{posici\'on} (Liu) ni por \alert{cantidad} (Mu).
\end{column}
\end{columns}

\end{frame}
```

- [ ] **Step 2: Compile and view**

```bash
xelatex -interaction=nonstopmode presentacion-instancia2.tex && open presentacion-instancia2.pdf
```

Expected: slide 4 with U-curve plot on left, Mu summary on right.

- [ ] **Step 3: Review**

The plot is illustrative, not a literal reproduction of Liu's data. If a profe asks "is this exact?", say "es esquem\'atico, basado en la curva del paper".

- [ ] **Step 4: Commit**

```bash
git add presentacion-instancia2.tex
git commit -m "feat: slide 4 eje 2 mecanismo Liu Mu"
```

---

## Task 6: Slide 5 — Eje 3: Mitigaciones (tabla comparativa)

**Files:**
- Modify: `presentacion-instancia2.tex` (append)

- [ ] **Step 1: Add the frame**

```latex
\begin{frame}{Eje 3 --- Mitigaciones existentes}

\renewcommand{\arraystretch}{1.3}
\begin{table}
\centering
\scriptsize
\begin{tabular}{@{} p{3.2cm} p{3.4cm} p{1.8cm} p{3.2cm} @{}}
\toprule
\textbf{M\'etodo} & \textbf{Idea} & \textbf{Costo} & \textbf{Limitaci\'on} \\
\midrule
Jerarqu\'ia de instrucciones\\
{\scriptsize(Wallace et al., 2024 --- OpenAI)} &
    System $>$ User, prioridad est\'atica &
    Cero extra &
    No aborda decay temporal \\

Repetir prompt cada turno &
    Re-inyectar todo &
    $N\times$ tokens &
    Saturaci\'on (Mu, 2025) \\

Duplicar prompt\\
{\scriptsize(Google Research, 2025)} &
    Instrucciones 2$\times$ &
    $2\times$ tokens &
    Refuerzo uniforme \\

Recordatorios peri\'odicos\\
{\scriptsize(Dongre et al., 2025)} &
    Re-inyectar cada $k$ turnos &
    $k$-dependiente &
    Mismo refuerzo a todas \\
\bottomrule
\end{tabular}
\end{table}

\vspace{0.6em}

\begin{center}
\footnotesize
Ninguna decide \alert{\textbf{qu\'e}} reforzar.
\end{center}

\end{frame}
```

- [ ] **Step 2: Compile and view**

```bash
xelatex -interaction=nonstopmode presentacion-instancia2.tex && open presentacion-instancia2.pdf
```

Expected: slide 5 with 4-row comparative table. This is the slide that most directly addresses the consigna's "comparación de métodos".

- [ ] **Step 3: Review**

If the table looks cramped, reduce font to `\tiny` or split limitation column. Read each row aloud — does the limitation column actually capture the limitation, or is it generic?

- [ ] **Step 4: Commit**

```bash
git add presentacion-instancia2.tex
git commit -m "feat: slide 5 eje 3 tabla comparativa mitigaciones"
```

---

## Task 7: Slide 6 — Eje 4 + vacancia

**Files:**
- Modify: `presentacion-instancia2.tex` (append)

- [ ] **Step 1: Add the frame**

```latex
\begin{frame}{Eje 4 --- Marco Bayesiano $\to$ Vacancia}

\textbf{Zhang et al.\ (2025).} Los LLM se comportan como \emph{filtros bayesianos descontados} con factor $\gamma < 1$: el prior se subpondera frente a observaciones recientes. Marco probabil\'istico para pensar el olvido.

\vspace{0.8em}

\textbf{Corbett \& Anderson (1994).} \emph{Bayesian Knowledge Tracing}: 30 a\~nos de uso en educaci\'on. Estima la probabilidad de mastery por concepto, turno a turno.

\vspace{1em}

\begin{block}{Vacancia detectada}
\begin{itemize}
    \item Nadie aplic\'o BKT a compliance de LLMs.
    \item M\'as importante: \alert{nadie midi\'o si el decay es heterog\'eneo entre instrucciones.}
    \item Sin esa premisa, un sistema BKT selectivo no se justifica.
\end{itemize}
\end{block}

\end{frame}
```

- [ ] **Step 2: Compile and view**

```bash
xelatex -interaction=nonstopmode presentacion-instancia2.tex && open presentacion-instancia2.pdf
```

Expected: slide 6 with two bridge papers and a `block` environment containing the gap.

- [ ] **Step 3: Review**

The block is the climax of the lit review. Read it aloud. The third bullet is the bridge to slide 7 — make sure it sounds like a question that needs answering, not a verdict.

- [ ] **Step 4: Commit**

```bash
git add presentacion-instancia2.tex
git commit -m "feat: slide 6 eje 4 vacancia bayesian framing"
```

---

## Task 8: Slide 7 — Orientación + JAIIO insight

**Files:**
- Modify: `presentacion-instancia2.tex` (append)

- [ ] **Step 1: Add the frame**

```latex
\begin{frame}{Orientaci\'on del proyecto final}

Antes de proponer un sistema BKT selectivo, hab\'ia que verificar el supuesto de \alert{heterogeneidad}.

\vspace{0.8em}

\textbf{Estudio emp\'irico que corr\'i:}
\begin{itemize}
    \item 28 conversaciones $\cdot$ 244 observaciones $\cdot$ 5 modelos
    \item Modelo log\'istico ordinal bayesiano, efectos jer\'arquicos por tipo de decisi\'on
    \item \textbf{Resultado:} $\sigma_\beta = 2.11$, HDI 94\% $[1.06,\ 3.28]$ $\to$ la heterogeneidad existe
\end{itemize}

\vspace{0.6em}

\textbf{Pr\'oximo paso del proyecto final:}
construir el sistema BKT con presupuesto fijo de tokens y testearlo contra refuerzo uniforme.

\vspace{0.8em}

\footnotesize\itshape
Trabajo sometido a JAIIO 2026, en revisi\'on. No es resultado validado por pares todav\'ia.

\end{frame}
```

- [ ] **Step 2: Compile and view**

```bash
xelatex -interaction=nonstopmode presentacion-instancia2.tex && open presentacion-instancia2.pdf
```

Expected: slide 7. The honesty disclaimer at the bottom is intentional — keep it.

- [ ] **Step 3: Review**

This is the most personal slide. Read it as if a profesor sceptical of self-citation is in the audience. Does it land as "honest researcher confirming a premise" or as "self-promotion"? If it leans promotional, soften.

- [ ] **Step 4: Commit**

```bash
git add presentacion-instancia2.tex
git commit -m "feat: slide 7 orientacion proyecto final con insight JAIIO"
```

---

## Task 9: References appendix

**Files:**
- Modify: `presentacion-instancia2.tex` (append after slide 7)

- [ ] **Step 1: Add the appendix**

```latex
\appendix

\begin{frame}{Referencias}

\scriptsize
\begin{columns}[T]
\begin{column}{0.48\textwidth}
Laban, P.\ et al.\ (2025). \emph{LLMs Get Lost in Multi-Turn Conversation}.\par\medskip
He, B.\ et al.\ (2024). \emph{Multi-IF: Benchmarking LLMs on Multi-turn and Multilingual Instruction Following}. Meta.\par\medskip
Chroma Research (2025). \emph{Context Rot}. Industria.\par\medskip
Liu, N.\ F.\ et al.\ (2024). \emph{Lost in the Middle: How Language Models Use Long Contexts}. TACL.\par\medskip
Mu, N.\ et al.\ (2025). \emph{System Prompt Robustness}.\par
\end{column}

\begin{column}{0.48\textwidth}
Wallace, E.\ et al.\ (2024). \emph{The Instruction Hierarchy}. OpenAI.\par\medskip
Google Research (2025). \emph{Prompt Repetition Improves Non-Reasoning LLMs}.\par\medskip
Dongre, M.\ et al.\ (2025). \emph{Periodic Reminders for Instruction Stability}.\par\medskip
Zhang, S.\ \& Yang, Y.\ (2025). \emph{LLMs as Discounted Bayesian Filters}.\par\medskip
Corbett, A.\ T.\ \& Anderson, J.\ R.\ (1994). \emph{Knowledge Tracing}. UMUAI.\par
\end{column}
\end{columns}

\end{frame}
```

- [ ] **Step 2: Compile and view**

```bash
xelatex -interaction=nonstopmode presentacion-instancia2.tex && open presentacion-instancia2.pdf
```

Expected: 8 slides total (7 + references). Verify references list is complete (9 entries — note Chroma counts as one even though it's industry).

- [ ] **Step 3: Verify each citation matches a slide mention**

Cross-check: every paper in the references should appear by name on slides 3-7. If you cite a paper in references that you never mention aloud, remove it from references. If you mention a paper aloud that's missing here, add it.

- [ ] **Step 4: Commit**

```bash
git add presentacion-instancia2.tex
git commit -m "feat: references appendix for instancia2"
```

---

## Task 10: Makefile + PPTX build

**Files:**
- Create: `Makefile`

- [ ] **Step 1: Check if a Makefile already exists**

```bash
ls Makefile 2>&1
```

If one exists, you'll add a target. If not, you'll create one.

- [ ] **Step 2: Create or extend the Makefile**

If the file does not exist, create `Makefile` with this content:

```makefile
.PHONY: instancia2-pdf instancia2-pptx instancia2-clean

instancia2-pdf: presentacion-instancia2.tex
	xelatex -interaction=nonstopmode presentacion-instancia2.tex
	xelatex -interaction=nonstopmode presentacion-instancia2.tex

instancia2-pptx: instancia2-pdf
	bash tools/pdf2pptx/pdf2pptx.sh presentacion-instancia2.pdf

instancia2-clean:
	rm -f presentacion-instancia2.aux presentacion-instancia2.log \
	      presentacion-instancia2.nav presentacion-instancia2.out \
	      presentacion-instancia2.snm presentacion-instancia2.toc \
	      presentacion-instancia2.pdf presentacion-instancia2.pdf.pptx
```

If a Makefile exists, append the three targets above.

- [ ] **Step 3: Run the full build**

```bash
make instancia2-clean
make instancia2-pptx
```

Expected:
- xelatex runs twice (second pass for refs/TOC)
- `presentacion-instancia2.pdf` exists
- `pdf2pptx.sh` runs and outputs `presentacion-instancia2.pdf.pptx`

If `pdf2pptx.sh` fails complaining about `pdftoppm` missing:
```bash
brew install poppler
```
Then re-run `make instancia2-pptx`.

- [ ] **Step 4: Open the PPTX in Keynote/PowerPoint to confirm**

```bash
open presentacion-instancia2.pdf.pptx
```

Expected: 8 image-slides. Click through each one. They should match the PDF exactly.

- [ ] **Step 5: Commit**

```bash
git add Makefile
git commit -m "build: makefile target for instancia2 pdf and pptx"
```

---

## Task 11: Dry-run cronometrado

**Files:** none (this is a behavioral check)

- [ ] **Step 1: Time yourself**

Open the PDF in presenter mode (`open -a Preview presentacion-instancia2.pdf` then full screen, or use Beamer's presenter mode if you compile with the `\usepackage{pgfpages}` option).

Start a stopwatch. Talk through the 7 content slides as if presenting. Don't read — present.

- [ ] **Step 2: Record the time**

Aim: 4:30–5:00. Note where you went too long or too short.

- [ ] **Step 3: If over 5:00 — trim**

Most likely places to cut:
- Slide 5 row 2 ("Repetir prompt cada turno") — combine into the synthesis line, drop the row.
- Slide 4 right column — remove Mu summary, keep only Liu's plot and a one-liner about Mu.
- Slide 7 bullet list — collapse to two bullets.

After trimming, recompile and re-run the dry-run.

- [ ] **Step 4: If under 4:00 — add depth, don't add slides**

Add 1-2 sentences per slide where you're being too terse. Don't add new slides — the structure is the contract.

- [ ] **Step 5: Final commit**

```bash
git add presentacion-instancia2.tex
git commit -m "tweak: trim instancia2 slides after dry-run timing"
```

(skip if no changes were needed)

---

## Task 12: Submit

**Files:** none (delivery action)

- [ ] **Step 1: Final build**

```bash
make instancia2-clean
make instancia2-pptx
```

- [ ] **Step 2: Verify file size and integrity**

```bash
ls -la presentacion-instancia2.pdf.pptx
file presentacion-instancia2.pdf.pptx
```

Expected: file exists, type is "Microsoft PowerPoint 2007+".

- [ ] **Step 3: Upload to the cátedra link**

Upload `presentacion-instancia2.pdf.pptx` to the link from the email (`CD-2026_Nodo-Tematico_Instancia-II`).

Deadline: 2026-05-07.

- [ ] **Step 4: Tag the commit**

```bash
git tag instancia2-submitted
git log -1
```

---

## Self-review (done by planner)

**Spec coverage:** all 7 slides + references + build pipeline + dry-run + submission covered (tasks 1-12). The "white theme" decision is in Task 1's preamble. The image-PPT pipeline is in Task 0 + Task 10.

**Placeholders:** none. Every code block is complete. No "TBD"s.

**Type consistency:** color `accent` defined in Task 1 (preamble), used in tasks 3, 4, 5, 6, 7, 8. File path `presentacion-instancia2.tex` consistent throughout.

**Open trade-off:** the prose in each slide is my best draft, not your voice. Each task ends with a "Review prose" step. Treat my LaTeX as scaffolding, your wording is the deliverable.
