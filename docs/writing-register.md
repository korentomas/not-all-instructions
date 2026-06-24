# Writing register — empirical AI-safety papers

A reusable style spec for prose in this line of work. Source register: **PowerBench**
(Brau, Gimenez Molina, Heredia, Korenblit et al., 2026) as the primary exemplar, with
framing cues from **Epoch AI** (data-first, neutral, evidence-grounded) and **Sequent**
(principled confidence, calibrated epistemic humility, "obstacles" honesty).

Use this when drafting or revising any paper, abstract, or report in the repo. It is a
checklist, not a template — apply the rules, don't copy the phrasing.

> Open question: the third source the author named ("afterthought") is not yet
> identified as a specific org/blog. Update this file once pinned down.

---

## 1. The voice in one line

Plain, declarative, measured. Every claim carries its evidence and its uncertainty.
No hype, no narrative flourish; the reader trusts it because it never oversells.

## 2. Rules (with PowerBench evidence)

**R1 — Operational definitions, inline, on first use.** Define a construct by what it
*does*, the moment it appears.
> "Disempowerment is when the requester seeks only to reduce a third party's power, with no benefit to themselves."

**R2 — State what a comparison isolates.** Don't just describe the design; say what it
buys you.
> "Comparing the three isolates the contribution of self-benefit from that of disempowerment."

**R3 — Numbers travel with their test and their uncertainty, inline.** Never a bare
point estimate.
> "the refusal rate was 35.0% for power-grabbing and 4.8% for harmless-empowerment (McNemar paired test, OR = 25.9, 95% CI [19.3, 34.8], p < 10⁻²⁰⁰)."

**R4 — Calibrated hedging; separate established from preliminary.** Grade your own
confidence explicitly.
> "This result comes from testing only two models ... so we read it as a pilot-level signal rather than an established finding."

**R5 — Plain declaratives; semicolons join a claim to its qualifier or consequence.**
Short-to-medium sentences. Minimal em-dashes. Cut inflation words (novel, powerful,
crucial, groundbreaking, significant-as-praise).

**R6 — Safety stakes up front, concrete, and cited.** Motivate from real consequences
and the published norms/literature, not from "this is interesting."
> "Concentrated power that becomes entrenched has been identified as a catastrophic-risk pathway for advanced AI [5, 4]. ... Both Anthropic and OpenAI have articulated this expectation in their published norms [1, 2]."

**R7 — Contributions enumerated.** "Our contributions are: (i) ... (ii) ... (iii) ...".

**R8 — Limitations are exhaustive and self-critical.** Name every confound plainly;
admit when your measures are proxies.
> "Our operationalizations ... are likely proxies for the more precise concepts these terms denote."

**R9 — Active "we"; past tense for what you did, present for what holds.**

**R10 — Interpretations are offered, not asserted.** "A possible interpretation is
that ..."; "If this holds, ...". Mechanism is explained, not just reported.

**R11 — One claim per paragraph, topic sentence first.** The paragraph then supplies the
number, the test, and the qualifier.

**R12 — Reproducibility is stated flatly** (temperature, effort, token caps, exclusions,
seeds), without apology or padding. See PowerBench §A.3.

## 3. Framing cues from the orgs

- **Epoch AI** — neutrality and evidence. Present measurement as a shared factual
  foundation ("grounded in the best possible evidence"), not advocacy. Let the numbers
  carry the argument.
- **Sequent** — principled vs reactive. Frame work as building *principled* grounds for
  belief before acting, and be honest when results are obstacles rather than solutions.
  Epistemic humility is a feature: "we are not confident that X will work."

## 4. Anti-patterns (strip these)

- Adjective inflation and "rule of three" lists used for rhythm.
- Vague attribution ("studies show", "it is well known") without a cite.
- Em-dash overuse; replace with semicolon/colon/period.
- A result stated without its test or its interval.
- Conflating a strong finding and a preliminary one in the same confident tone.
- Narrative throat-clearing ("In recent years, AI has...").

---

## 5. Applying this to *Not All Instructions Are Forgotten Equal* (AIS angle)

The user wants the AIS framing **substantial**, the way PowerBench leads with power
concentration. Concrete hooks (detailed per-section edits pending the audit + approval):

- **Reframe the stakes around guardrail decay.** Guardrails are instructions; if
  instruction compliance decays unevenly over long context, then safety-relevant
  instructions can decay *silently* while the model keeps responding. This is the
  PowerBench move: tie the measurement to a recognized risk and cite the norms
  (Anthropic/OpenAI) and the many-shot-jailbreak / context-length-safety literature.
- **"Safety doesn't transfer across context length"** — mirror PowerBench's "safety does
  not transfer across languages." Same shape: a known per-axis non-transfer of safety
  behavior, here the axis is conversation length / position.
- **Principled before reactive (Sequent).** Current mitigations (repeat-everything,
  fixed reminders) are reactive and uniform; this paper supplies the *principled*
  per-instruction measurement that a selective control policy would need. Frame selective
  reinforcement as an oversight/control mechanism under a token budget.
- **Neutral, evidence-first (Epoch).** Keep the heterogeneity result as a measured fact;
  let σ_β and the per-decision intervals carry it; avoid overclaiming the BKT system,
  which is not built here.
- **Honest obstacle (Sequent).** The negation backfire (`dependencies_no_new`) is an
  obstacle worth foregrounding, not burying — stating a safety rule can reduce
  compliance. That is a safety-relevant failure mode, framed with calibrated uncertainty.
