# Humanizer pass — paper.tex

Detect-only scan of LLM-y patterns in `paper/paper.tex`. Attacking one by one.
Status: `[ ]` open · `[~]` in progress · `[x]` done · `[-]` won't fix (defensible)

## P1 — Contrastive "X, not Y" / "rather than" frame (density tell)
~7 instances. Each fine alone; clustering is the signature. Goal: thin out / vary,
keep the 2-3 that carry real argumentative weight.

- [-] L42  "deterministic checkers rather than an LLM judge" — KEEP, core method claim
- [x] L160 → "we read this cautiously: the design shows model-invariance, but cannot establish that model effects are absent"
- [x] L478 → "we suspect a measurement artifact here and do not read it as a robust harm"
- [x] L514 → "This posterior-derived ranking identifies... ; we do not run it as a closed-loop policy"
- [-] L529 "a cost criterion, not a safety one" — KEEP, thesis
- [-] L533 "It saves tokens... does not choose which guardrails" — KEEP, thesis
- [x] L710 → "no detectable effect at this resolution; we do not claim established invariance"

## P2 — Rule-of-three triads (low risk, factual lists)
- [x] L104 → "run for hundreds of turns in a loop, calling tools with no human reviewing each step" (triad broken)
- [ ] L223 "read files, write code, search the codebase" — **STILL OPEN**. 2/3 agents EDIT but no agreed form (Scrub: compress; Voice: drop "search"→2). Lead leaned KEEP (genuine tool-affordance list). NEEDS DECISION.
- [-] L413 "conversation logs, checker code, and analysis notebooks" — KEEP (2/3 agents agree: distinct artifact classes, reproducibility inventory)

## P3 — Word repetition "real"/"realistic" — RESOLVED
- [x] L123 "effects are real" → cut (batch)
- [x] L149 "realistic multi-turn" → dropped "realistic"
- [-] L222 "real open-source" — KEEP, meaningful real-vs-synthetic
- [x] L369 "real file contents" → "file contents" (batch)
- [x] L695 "real coding-session traces" → "traces from deployed coding sessions" (batch)

## Subagent experiment (3 priors, Sonnet, read-only proposals) — DONE
Scrubber (aggressive) · Preservationist (conservative) · Voice (specificity).
Lesson: fault line was "real" (x6). Preservationist defended all as real-vs-synthetic
contrast; Scrubber+Voice flagged filler. Truth mixed — some cut, some sharpen wording.
Voice over-reached injecting numbers into sections where figure lives elsewhere.

Applied batch (6 edits, rebuilt clean exit=0):
- [x] L122 "effects are real and often irreversible" → "effects are often irreversible"
- [x] L226 "building up context pressure as the conversation progresses" → "to build context pressure"
- [x] L368 "serves real file contents" → "serves file contents"
- [x] L393 "Qwen served as the primary model" → "Qwen was the primary model,"
- [x] L641 "real guardrails" → "actual guardrails"
- [x] L694 "real coding-session traces" → "traces from deployed coding sessions"
- [-] L529 "cost criterion" → "token-cost" — SKIPPED (user unsure)
- [-] L225 "Real source files" head — left (not approved)
- [-] #1,#2,#8,#10, L584 — kept (defensible / thematic)

"real" count: 6 → 1 (only L225 head remains).

## P4 — Minor — RESOLVED
- [x] L227 "building up context pressure..." → "to build context pressure" (batch, was #6)
- [-] L119 "safety concern before it is a cost concern" — KEEP, reads human
- [x] L393 "Qwen served as the primary model" → "Qwen was the primary model," (batch, was #7)

## Final batch (4 edits) — DONE, rebuilt clean exit=0
- [x] L224 triad → "(read and write code, search the codebase)" (3 beats → 2)
- [x] L225 "Real source files" → "Source files" (last filler "real"; matches Setup L367)
- [x] L528 "is a cost criterion, not a safety one" → "guides token spending, not safety decisions" (user disliked old phrasing)
- [x] L582 "This raises the question of whether" → "It is unclear whether" (vague opener killed)

## USER PREFERENCE LEARNINGS (this session)
1. **REJECT the "X, not Y" / negative-parallelism contrast frame** even when load-bearing.
   Rejected BOTH "cost criterion, not a safety one" AND "guides token spending, not safety
   decisions" — the frame itself is the tell, not just the wording.
2. Avoid abstract nominalizations ("criterion", "decisions", "token spending"). Concrete verbs/objects.
3. Plain copula > elaborate; specific > vague; tight, no padding.
4. Approved-style exemplars: "Qwen was the primary model" · "It is unclear whether..." · "to build context pressure".

## DEEP PASS on L528 (cost-vs-safety sentence) — IN PROGRESS
Phase 1 (3× Opus 4.8) DONE — 9 candidates. Phase 2 (Sonnet evaluators) running.

Original (rejected): "This ranking guides token spending, not safety decisions: a low gain
may mean the model already complies, or that the checker saw nothing (a default-2 ceiling),
neither of which licenses dropping a safety-relevant rule."

Cut/Merge (opus_cut, best=A1):
- A1: "A low gain may mean the model already complies, or that the checker saw nothing (a default-2 ceiling), neither of which licenses dropping a safety-relevant rule." [opening clause deleted]
- A2: "But a low gain may only mean the model already complies, or that the checker saw nothing (a default-2 ceiling); neither reason licenses dropping a safety-relevant rule."
- A3: "A low gain pushes an instruction down the reinforcement list, but it may only mean the model already complies, or that the checker saw nothing (a default-2 ceiling); none of that licenses dropping a safety-relevant rule."

Declarative (opus_declarative, best=B1):
- B1: "The ranking only marks where reinforcement is wasted: a low gain can mean the model already complies, or that the checker saw nothing (a default-2 ceiling), and a safety-relevant rule stays in the prompt either way."
- B2: "The ranking locates wasted reinforcement and nothing else: a low gain can mean the model already complies, or that the checker saw nothing (a default-2 ceiling), and neither reading licenses dropping a safety-relevant rule."
- B3: "The ranking points to rules where reinforcement does little, and a low gain there says nothing about safety: it can mean the model already complies, or that the checker saw nothing (a default-2 ceiling), so a safety-relevant rule stays stated regardless."

Concrete-verb (opus_concrete, best=C1):
- C1: "The ranking shows where reinforcement earns its tokens; a low gain never marks a rule as safe to drop, since the model may already comply or the checker may have seen nothing (a default-2 ceiling)."
- C2: "The ranking points to rules where reinforcement saves tokens; it cannot tell us to stop stating a safety-relevant rule, since a low gain may only mean the model already complies or that the checker saw nothing (a default-2 ceiling)."
- C3: "A low gain can mean the model already complies, or that the checker saw nothing (a default-2 ceiling); either way the ranking only marks where we can save tokens and never clears a safety-relevant rule for removal."

NOTE: next sentence already says "It saves tokens on ordinary preferences; it does not choose
which guardrails to stop stating" → candidates that re-say "saves tokens" risk redundancy.

## DONE (earlier batches)
"real" count: 6 → 2, both legit (L222 genuine-vs-synthetic anchor; L677 "real-time" compound).
Full pass tally: P1 4 edits, P2 2 edits, P3 4 edits, P4 2 edits, final 4 edits = 16 prose edits + figures untouched.
Paper rebuilds clean. Uncommitted: paper.tex, references.bib.

## Clean (no action)
- No em-dash overuse · no buzzwords · no chatbot artifacts · no curly quotes.
- Acks flowery but deliberately personal — not AI.

## Notes
- Line numbers drift as edits land; re-grep before each edit.
- Rebuild PDF after batch: `latexmk -pdf -bibtex -cd paper/paper.tex`
