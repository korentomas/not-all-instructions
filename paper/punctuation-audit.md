# Punctuation audit — paper.tex

Scope: every semicolon, colon, dash, and minus flagged in review. Goal: decide
keep vs. cut. Counts are raw `.tex` (includes LaTeX syntax). Verdict column is a
first-pass suggestion, not final.

Legend — **KEEP** = good as-is · **REVIEW** = candidate to rephrase · **N/A** = syntactic (LaTeX), not prose.

---

## Semicolons — 7 total (6 prose + 1 syntactic)

| Line | Snippet | Type | Verdict |
|---|---|---|---|
| 116 | "...a chat user notices and restates it**;** a deployed agent has no such supervisor..." | prose, contrast | REVIEW — could be period or "whereas" |
| 323 | `\parencite[NUTS;][]{hoffman2014}` | cite arg | N/A |
| 519 | "It saves tokens on ordinary preferences**;** it says nothing about which guardrails to drop." | prose, balance | KEEP — tight parallel, intentional |
| 566 | "...its direction is credible ($P(\beta<0)=0.98$)**;** the magnitude... remain open." | prose, two indep clauses | REVIEW — long clause, period may read cleaner |
| 707 | ack: "...unwavering support**;** my caring family..." | series w/ internal commas | KEEP — needs semicolon (list items contain commas) |
| 708 | ack: "...all the way here**;** my alma mater..." | series | KEEP — same series |
| 709 | ack: "...halls I still live**;** and all my teachers..." | series | KEEP — same series |

Note: 3 ack semicolons are one structure → can't split without breaking the list.
Real discretionary prose semicolons = lines 116, 519, 566.

---

## Dashes

### Em-dash `---` — 4, ALL in LaTeX comments
| Line | Context | Verdict |
|---|---|---|
| 20 | `% --- ENGLISH TITLE... ---` | N/A (comment) |
| 56 | `% --- SPANISH TITLE ---` | N/A (comment) |

Zero em-dashes in body prose. Clean (humanizer/LNCS happy).

### En-dash `--` — 12, all legit ranges/compounds
| Line | Use | Verdict |
|---|---|---|
| 40, 249, 272 | `0--3` (score scale) | KEEP |
| 219, 357 | `0--19` (turns) | KEEP |
| 223 | `1--7`, `14--19` | KEEP |
| 238, 642 | `20--25` (turns) | KEEP |
| 672 | `checker--judge` (compound) | KEEP |
| 375, 376 | table `--` = empty cell (undisclosed param) | KEEP |

### Math minus `$-` — 6, negative stats
| Line | Value | Verdict |
|---|---|---|
| 42 | `$-2.4$` (EN abstract, log-odds span) | KEEP |
| 77 | `$-2{,}4$` (ES abstract, comma decimal) | KEEP |
| 150 | `$-2.4$` (intro) | KEEP |
| 431 | `$-2.36$` (results, forest) | KEEP |
| 540 | `$-$0.47` (policy table) | KEEP |
| 599 | `$-228.8$` (ELPD, LOO-CV) | KEEP |

Dashes overall: clean. No misuse, nothing to cut.

---

## Colons — 84 total (30 syntactic + 54 prose)

### Syntactic — 30 (N/A, do not touch)
- `\label{sec:...}` / `\ref` — 29
- `https:` URL — 1

### Prose colons — 54, by category

#### A. Rhetorical (clause → elaboration) — ~17, the discretionary ones
| Line | Snippet | Verdict |
|---|---|---|
| 102 | "governed by its instructions**:** the operational limits..." | REVIEW |
| 107 | "The cause is architectural**:** attention is not..." | KEEP — crisp |
| 141 | "We adapt this framing**:** the LLM is the student..." | KEEP |
| 156 | "we read this cautiously**:** the design shows model-invariance..." | REVIEW |
| 180 | "U-shaped attention curve**:** information at the beginning..." | KEEP |
| 184 | "a related saturation effect**:** as the number of guardrails..." | KEEP |
| 224 | "different coding practice**:** code style (NumPy...)" | KEEP — intro to list |
| 273 | "unequal intervals**:** the gap between 0..." | KEEP |
| 442 | "into three groups**:**" | KEEP — list intro |
| 553 | "Retention tracks default behavior**:** instructions that ask..." | KEEP |
| 573 | "determines the fix**:** if negation is the problem..." | REVIEW |
| 628 | "One direct test remains open**:** whether a stated safety constraint..." | KEEP |
| 230 | "(e.g., ``Important**:** when writing array operations...)" | KEEP — inside quoted prompt |
| 353 | "cloned at fixed commits**:** Bambi..." | KEEP — list intro |
| 391 | "28 conversations in total**:** 9 baseline and 19 treatment" | KEEP |
| 412 | "converged cleanly**:** zero divergences..." | KEEP |
| 491 | "One reading we can set aside, though**:** retention does not climb..." | REVIEW |

#### B. List / item labels — ~12 (structural, keep)
| Line | Snippet |
|---|---|
| 249 | "ordinal score on a 0--3 scale**:**" |
| 252–255 | `\item \textbf{0}:` / `1:` / `2:` / `3:` (score defns) |
| 340 | "context pressure levels**:**" |
| 343 / 346 / 349 | bullet defns: Bambi**:** / ArviZ**:** / PyMC**:** |

All KEEP — itemize structure.

#### C. Stat / HDI parentheticals — ~13 (keep, convention)
| Line | Snippet |
|---|---|
| 429 | "94\% HDI**:** $[1.06, 3.28]$" |
| 447 | "HDI**:** $[2.94, 8.10]$**:** models almost never..." (2 colons) |
| 449 | "(treatment mean**:**" |
| 451 / 453 | "HDI**:** $[...]$" |
| 476–477 | "broadcasting**:** 3.00, numpy\_style**:** 3.00...**:** the models already..." |
| 652 | "default-2 rates above 50\%**:** architecture\_extend (79\%)" |

KEEP — stat notation; the `HDI: [...]:` double on 447/453/477 worth a glance (colon doing two jobs in one sentence).

#### D. Figure-caption labels — ~6 (keep)
| Line | Snippet |
|---|---|
| 420 / 421 | "Left**:**" / "Right**:**" |
| 438 / 508 | "Dark bars**:**" / "Hatched**:**" |

KEEP — caption convention.

---

## Summary — what to actually look at

Cut candidates (discretionary, may over-punctuate):
- **Semicolons:** lines 116, 566 (long clauses → try period). 519 keep.
- **Colons:** lines 102, 156, 491, 573 (REVIEW — back-to-back colon sentences in
  intro/discussion can feel listy). 447/453/477 — colon doing double duty in one
  sentence.

Definitely keep:
- All dashes (clean).
- Ack semicolons (707–709) — required by comma-laden list.
- All list/caption/stat colons (structural).

Open question for analysis: density per page. ~17 rhetorical colons + 3 prose
semicolons across ~14pp is moderate. Risk is *clustering* (e.g. intro §1 has
colons on 102/107 + Discussion has 553/573/491 close together), not raw count.

---

## Connective-word reference (replace colon / semicolon / em-dash)

Goal: shift punctuation joins into single connective words. No em-dashes at all.

### Contrast (replace `;` or `, but`)
whereas · while · though · although · yet · even as · albeit (one-word concession) · notwithstanding

### Relative / appositive (replace `:` defining a noun)
which · whose · where · in which · by which · through which · whereby (by which means) ·
wherein (in which) · whereof (of which) · whereupon (after which) · whereat (at which point)

### Cause / premise (replace `:` explanation)
because · since · as · given that · seeing that · in that ("useful in that it…") ·
inasmuch as · for (literary "because")

### Degree / extent (replace `:` qualifying a claim)
insofar as · inasmuch as · to the extent that

### Apposition / naming (replace `:` before a definition)
namely · that is · is that ("the reading is that…")

### Result / consequence (replace `:` or `;`)
so · thus · hence · therefore · thereby ("thereby reducing cost") · such that · whence (from which)

### Addition / sequence (replace `;`)
moreover · furthermore · whereupon

### Condition / exception
provided that · so long as · save that · except that · lest

**Paper sweet spot (formal, uncommon, reviewer-safe):**
whereas · whose · where · whereby · wherein · in that · insofar as · albeit · thereby · namely · whereof

**Avoid (read as archaic / pretentious to reviewers):**
whither · wherefore · whence · whereat · thence

Sources: QuillBot subordinating-conjunctions; Cambridge Dictionary grammar;
Grossmont College subordinators; Academic English UK linking words.

---

## Edit log

### Round 1 — semicolons (prose, applied)
| Line | Was | Fix |
|---|---|---|
| 116 | `;` contrast | whereas |
| 519 | `;` balance | but |
| 566 | `;` two clauses | period split ("What stays open is…") |
| 707–709 | `;` ack series | KEPT (comma-laden list forces them) |
| 323 | `[NUTS;]` | KEPT (cite arg) |

### Round 2 — a–k rhetorical colons (applied)
| # | Line | Connective used |
|---|---|---|
| a | 102 | which are |
| b | 107 | lies in the architecture, where |
| c | 141 | where |
| d | 156 | because |
| e | 180 | where |
| f | 184 | whereby |
| g | 273 | period split |
| h | 553 | period + whereas |
| i | 573 | period split |
| j | 491 | is that |
| k | 628 | namely |

### Round 3 — double-duty colons (stat-colon + rhetorical, applied)
| Line | Fix |
|---|---|
| 447 | where + dropped 2 inner `mean:` colons |
| 453 | of … and |
| 477 | period split (inner `broadcasting: 3.00` labels kept) |

### Round 4 — missed rhetorical colons (applied)
| Line | Connective |
|---|---|
| 392 | comprising |
| 413 | with |
| 626 | because |

### Round 5 — optional enumeration colons (applied)
| Line | Connective |
|---|---|
| 225 | spanning |
| 354 | namely |
| 443 | period |
| 588 | with |
| 653 | specifically |

### Kept as structural (justified, ~30 LaTeX + ~30 prose)
- LaTeX: `\label`/`\ref` (29), URL (1)
- Definition-style bullet labels: `Bambi:`, `ArviZ:`, `PyMC:` (344/347/350)
- Equation / itemize lead-ins: 250, 279, 290, 298, 303, 341
- Stat notation: `HDI:`, `mean:`, `broadcasting: 3.00` (430/448/452/454/477)
- Figure-caption tags: `Right:`, `Dark bars:`, `Hatched:` (422/439/509)
- Verbatim quoted prompt: `` ``Important: `` `` (231) — changing misreports the stimulus

### Final counts (verified, BUILD OK)
| | Start | End |
|---|---|---|
| Semicolons | 7 | 4 (all forced) |
| Colons | 84 | 60 (all structural) |
| Em-dash `---` | 4 | 4 (all `% comments`, zero prose) |

Connectives used, no clustering: whereas · which are · where · because · whereby ·
namely · is that · with · of/and · spanning · specifically · comprising · but ·
period splits.
