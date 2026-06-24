# JAIIO ASAID — Camera-ready + Futuro trabajo

**Paper 249 — "Not All Instructions Are Forgotten Equal" — ACEPTADO (ASAID, 55 JAIIO).**
Aceptación unánime (3/3): Reviewer #3 "Muy bueno (debe ser aceptado)"; #1 y #2 "Bueno (recomiendo que se acepte)".

## ⏰ DEADLINE — versión final / camera-ready

**Enviar versión final ANTES del 29 de junio de 2026.**
(Hoy: 2026-06-04 → quedan ~25 días.)

Lo que entra antes del 29/06 es **solo texto** (no hay tiempo ni necesidad de re-correr
experimentos para camera-ready). Los cambios computacionales con los créditos de Azure
($5k) son una **segunda fase, posterior** (paper extendido / journal), no el camera-ready.

## Resumen de las reviews (para qué accionar)

| | R1 | R2 | R3 |
|---|---|---|---|
| Eval general | Bueno (accept) | Bueno (accept) | **Muy bueno (debe aceptarse)** |
| Más bajo | Presentación/Claridad: Buena | Relev./Orig.: Buena | Claridad/Refs: Buena |
| Potencial I+D | Muy bueno | Muy bueno | Muy bueno |

Comentarios accionables:
- **R1**: "more real-world validation and broader baseline evaluation across all models."
- **R3**: evaluar, para las instrucciones con **HDI > 0** (las que se benefician), cuánto cambia
  la adherencia si se las **parafrasea a/desde la negación** → afila nuestro "negation analysis".
- **R2**: elogio puro, sin pedido.

---

## A) Camera-ready (texto, antes del 29/06)

Cambios baratos que responden a los revisores y suben Presentación/Claridad sin re-correr nada:

1. **Reforzar la sección de Future Work** con el bloque de abajo (responde explícitamente a R1 y R3
   → señal de que escuchamos a los revisores).
2. Una frase reconociendo el pedido de R3 en la Discussion (donde ya hablamos de la negación de
   `dependencies_no_new`), citando el diseño que propone.
3. (Opcional) Mover/expandir 1–2 frases de claridad en las secciones que los revisores marcaron
   más flojas.
4. Mantener consistencia con `trabajo-final.tex` (la versión de la materia) si la historia cambia.

### Bloque "Future Work" listo para pegar en `paper/paper.tex` (EN)

> **Future work.** Building on these results and reviewer feedback, we identify six directions.
>
> *Full-factorial baselines and broader model coverage.* Our baseline condition was collected for a
> single model (Qwen); extending matched baseline and treatment conditions to every model would let us
> estimate per-model effects directly and test whether the retention landscape is model-invariant,
> rather than inferring it from a single-model sensitivity analysis.
>
> *Triangulated, debiased compliance measurement.* The deterministic checkers are fully reproducible
> but have construct-validity limits (high default-2 rates for some decisions). Pairing them with a
> blinded panel of LLM judges drawn from model families distinct from those under evaluation — and
> reporting checker–judge and inter-judge agreement — would separate measurement bias from the effect
> of interest. As with the checkers, the judges should be blind to the planted instruction.
>
> *Disentangling phrasing from instruction type.* The only instruction harmed by reinforcement
> (`dependencies_no_new`) is also the only one phrased as a negation. As a reviewer suggested,
> re-running the instructions whose treatment effect excludes zero under negated paraphrases — and the
> negated instruction under positive paraphrases — would measure within-instruction phrasing variance
> against between-instruction variance, isolating whether negation framing, rather than content,
> drives the effect.
>
> *Dense temporal measurement.* Scoring compliance at every turn, rather than only at turns 20–25,
> would let us fit per-instruction forgetting curves and estimate decay rates (the discount factor
> in the BKT framework).
>
> *Closed-loop evaluation.* Implementing the posterior-derived reinforcement ranking as a runtime
> policy and measuring whether selective reinforcement beats uniform reinforcement under a fixed
> token budget.
>
> *Ecological validity.* Replacing simulated planting with traces from real coding sessions would
> test whether the retention structure observed here holds outside the harness.

---

## B) Fase 2 — refinación experimental con $5k de Azure (POST camera-ready)

Objetivo: no "correr más", sino **eliminar sesgos nombrados** y apretar posteriors. Esto es el
material del paper extendido/journal, NO del camera-ready.

Sesgos a eliminar (cada uno con su fix):
1. **Baseline de un solo modelo** → factorial completo baseline×treatment para todos los modelos
   (recupera términos per-model/per-codebase que tuvimos que tirar por 267 divergencias). [R1]
2. **Validez de constructo de los checkers** → segundo canal de medición (LLM-judge sobre las 12
   decisiones) + reportar acuerdo κ checker–judge. Triangulación.
3. **Sesgo del juez** → HOY el judge es `qwen3.5-27b` = el modelo primario (self-bias). Fix: **panel
   ≥3 jueces cross-family, ciego a la condición Y a la instrucción plantada.**
4. **Wording / negación** → múltiples paráfrasis por instrucción (incl. flip positivo↔negación);
   separa varianza intra-instrucción (frase) de inter-instrucción (tipo). [R3, el de mayor valor]
5. **Posición de plantado** → counterbalance (cuadrado latino) early/late.
6. **Confound codebase/presión** → balancear todo modelo×codebase×condición; padear con tokens
   neutros para aislar presión de contenido.
7. **Estocasticidad** → réplicas por condición (seeds, temperatura fija).

Infra: modelos bajo test self-hosted en GPU de Azure (vLLM, paga GPU-hora) — el sumidero de costo
son los turnos 20–25 a ~200K tokens de contexto; jueces vía API frontier (Azure OpenAI). Pendiente:
**modelo de costos** (obs_objetivo × tokens/obs × precio) antes de fijar el factorial.

Decisiones abiertas antes de diseñar la Fase 2:
- ¿Camera-ready+journal-extendido, o paper nuevo centrado en negación + medición robusta?
- Lista de modelos (cobertura 7B→120B + 1–2 frontier de techo).
- ¿Self-hosting vLLM OK? (rinde 5–10× el presupuesto vs APIs por-token).
