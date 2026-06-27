# Deep-pipeline proposals (whole-paper) — 42 edits, FOR REVIEW

Workflow `wuzmh38dg`: 10 Sonnet detect + Opus generate (3 angles) + Sonnet judge. 46 detected → 42 EDIT, 4 lost to agent errors.
Pipeline rubric hard-rejected ALL contrast frames → more aggressive than this session's hand-tuned choices. NOTHING applied yet.

Tags: ✅ safe (pure cut/clear win) · 🟡 review (good, notable rewording) · 🔴 risky (meaning shift / conflicts with an earlier decision / needs ES check)

---

## 🔴 RISKY / CONFLICTS — decide individually

**R1. abstract-en — CONFLICTS with earlier KEEP**
quote: `grade compliance with deterministic checkers rather than an LLM judge`
→ `grade compliance with deterministic checkers`
Note: you + all 3 earlier priors KEPT this as the core method contrast vs prevailing LLM-judge practice. Pipeline wants it cut. **Recommend KEEP (override pipeline).**

**R3. abstract-en — abstract, number-bearing**
quote: `blanket reinforcement spends most of its tokens for no gain`
→ `restating every instruction wastes the tokens it costs on the other nine types`
Note: introduces "nine types" (12−3=9, consistent) but clunky in the abstract. Review wording.

**R5. abstract-es — Spanish, needs fluency check + mirror EN**
quote: `las reglas que el modelo no seguiría por sí solo son justamente las que un solo enunciado puede no asegurar`
→ `un solo enunciado no asegura las reglas que el modelo no aplica por defecto`

**R6. abstract-es — Spanish, slight meaning shift (esconde=hides vs no puede decir=cannot tell)**
quote: `una tasa de cumplimiento agregada no puede decir si la regla que importa sigue vigente`
→ `el promedio de cumplimiento esconde si la regla que importa sigue vigente`

**R15. method — drops "not system prompt rules" (methodologically relevant to guardrail-proxy argument)**
quote: `The instructions are phrased as natural user preferences, not system prompt rules (e.g., ...)`
→ `The user phrases each instruction as a natural preference (e.g., ...)`

**R23. results — logical-claim rewrite**
quote: `A larger model is not automatically a more compliant one, which is what we would need to see if these differences were a capability effect rather than a property of the instruction.`
→ `If these differences were a capability effect, the largest model would comply most.`
Note: clean counterfactual but drops the "and it doesn't" conclusion (judge says prior sentence carries it). Verify.

**R24. results — THESIS sentence (kept multiple times this session)**
quote: `It saves tokens on ordinary preferences; it does not choose which guardrails to stop stating.`
→ `It saves tokens on ordinary preferences; guardrails stay in the prompt whatever their gain.`

**R25. results — RE-EDITS my earlier fix; "reward reinforcement" awkward (judge admits)**
quote: `This posterior-derived ranking identifies which instructions would benefit from reinforcement; we do not run it as a closed-loop policy.`
→ `This ranking flags which instructions reward reinforcement; it is an offline diagnostic.`
Note: this is already my humanized version. Recommend KEEP mine unless you prefer "offline diagnostic".

**R34. limitations — KEY honesty caveat (preferences ≠ guardrails)**
quote: `ordinary coding preferences, not safety guardrails`
→ `ordinary coding preferences`
Note: central scoping caveat. Judge says next sentence recovers it. High-stakes cut.

**R35. limitations — drops the proxy-limitation contrast**
quote: `code style rather than a harmful action taken or avoided`
→ `how closely the generated code follows the planted style`

**R38. limitations — loses informative "not a decay curve"**
quote: `This gives a retention snapshot, not a decay curve.`
→ `It shows how much compliance survived to that window.`
Note: "not a decay curve" tells reader what they DON'T get — genuinely informative. Risky.

---

## ✅ SAFE — apply with confidence (8)

**S12. related** `The mechanism behind compliance degradation has roots in the attention architecture itself.` → `Compliance degradation arises from the attention architecture.`
**S13. related** `with each instruction in the role of a concept` → `where each instruction is a concept`
**S16. method** `working on a real open-source codebase` → `working on an open-source codebase` (cut "real", consistent w/ earlier)
**S19. method** `which is the premise selective reinforcement depends on` → `the condition selective reinforcement requires`
**S26. results** `near-zero baseline, meaningful retention when stated.` → `near-zero baseline, retention when stated.` (cut "meaningful")
**S29. discussion** `To address the concern that baseline data comes from Qwen only, we fit the same model restricted to Qwen observations (132 of 244, both conditions).` → `Baseline data comes from Qwen only, so we refit the model on Qwen observations alone (132 of 244, both conditions).`
**S31. discussion** `The treatment effects follow a pattern: instructions that ask for something the model would not do by default are retained when stated, while instructions that match existing behavior show no treatment effect.` → `Instructions that ask for something the model would not do by default are retained when stated; instructions that match existing behavior show no treatment effect.`
**S39. limitations** `so it speaks most directly to newly stated, in-context constraints` → `so our finding applies most directly to newly stated, in-context constraints`

---

## 🟡 REVIEW — good rewrites, notable rewording (23)

**V2. abstract-en** `Prior work reports mean compliance and reinforces every instruction uniformly; we measure retention per instruction instead.` → `We measure retention per instruction, where prior work reports only mean compliance and reinforces every instruction equally.`
**V4. abstract-en** `a model keeps following some and drops others, with nothing to flag the lapse` → `a model keeps following some and silently drops others`
**V7. intro** `We plant ordinary coding preferences rather than guardrails, but the two are the same kind of object` → `We plant ordinary coding preferences, and a preference and a guardrail are the same kind of object`
**V8. intro** `which we read as a likely measurement artifact rather than a robust harm` → `which most likely reflects a measurement artifact`
**V9. intro** `Bayesian Knowledge Tracing \parencite{corbett1994} offers a framework for exactly this kind of estimation.` → `Bayesian Knowledge Tracing \parencite{corbett1994} is a framework for per-instruction estimation.`
**V10. related** `None examines whether different instructions are retained to different degrees.` → `Whether some instructions survive longer than others remains untested.`
**V11. related** `Several recent studies have established that LLMs lose adherence to instructions as conversations grow.` → `As conversations grow, models follow fewer of their instructions.`
**V14. related** `Adherence therefore degrades unevenly: it depends on where an instruction sits and how many others surround it.` → `A model therefore follows a rule less reliably the deeper it sits and the more instructions crowd around it.`
**V17. method** `Checkers are fully automated with no LLM-in-the-loop evaluation.` → `Code alone assigns every score.`
**V18. method** `the conversation follows the same structure with the same file injections and the same task, but no preferences are planted.` → `we inject the same files and issue the same task, but plant no preferences.`
**V20. setup** `scores reflect a single draw, not an average.` → `each score comes from that single generation.`
**V21. setup** `All conversation logs, checker code, and analysis notebooks are available at` → `All data and code are available at` (NOTE: earlier this session this triad was KEPT)
**V22. results** `this is weak evidence of model-invariance, not a demonstration, and per-model retention cannot be fully separated` → `supports model-invariance only weakly, and we cannot fully separate per-model retention`
**V27. results** `do not read it as a robust harm` → `do not read it as evidence of harm` (my earlier edit; cuts "robust")
**V28. results** `meaning models already follow these conventions without prompting; reinforcing them does not change the score.` → `models already follow these conventions, and the instruction leaves the score unchanged.`
**V30. discussion** `We reduce the count of clearly beneficial decisions from three to two when considering only Qwen data.` → `Two decision types retain 94\% HDI entirely above zero in the Qwen-only data, down from three in the full model.`
**V32. discussion** `Distinguishing these hypotheses requires a controlled comparison that holds semantic content constant while varying the negation frame.` → `Distinguishing these hypotheses requires a controlled comparison that rephrases the same instruction with and without negation.`
**V33. limitations** `The sensitivity analysis ($r = 0.80$) mitigates but does not eliminate this concern.` → `The sensitivity analysis ($r = 0.80$) leaves this concern partly open.`
**V36. limitations** `that link is a hypothesis grounded in the shared mechanism, not a demonstrated guardrail bypass` → `that link remains a hypothesis grounded in the shared mechanism`
**V37. limitations** `Showing that a stated safety constraint decays the same way, and that the decay lets a harmful action through, is the experiment this paper motivates but does not run.` → `Our results motivate a further experiment: showing that a stated safety constraint decays the same way, and that the decay lets a harmful action through. We have not run it.`
**V40. limitations** `Building and evaluating such a system, including closed-loop token-budget allocation and real-time compliance tracking, is future work.` → `Such a system would reallocate token budgets through a feedback loop and track compliance as a run unfolds; we leave it to future work to build and evaluate.`
**V41. closing** `which would estimate per-model effects directly instead of inferring model-invariance from a single-model check` → `which would estimate per-model effects directly.`
**V42. closing** `Scoring every turn, rather than only 20--25, would fit per-instruction forgetting curves and decay rates.` → `Scoring every turn would fit per-instruction forgetting curves and decay rates.`

---

## Recommendation
1. Apply the 8 ✅ now (low risk).
2. Review 23 🟡 as a batch — mostly good; I'd take ~all with maybe 1-2 word tweaks.
3. Decide 11 🔴 one by one. My leans: KEEP R1 + R25 (override pipeline), and R34/R38 carry real meaning — lean KEEP. The rest of 🔴 are acceptable.
