# Port del harness a Inspect AI — `instruction-retention-bench`

**Objetivo:** convertir el harness de context-rot/retención en un eval dataset reproducible
y publicable en formato Inspect (UK AISI), corrible en la sub Azure Sponsored. Esto responde
a R1 (broader baselines, reproducible) de forma máxima y deja un benchmark citable.

Contexto: METR migró su suite entera a Inspect (ene-2026); Epoch publica task defs en Inspect;
Anthropic/DeepMind/xAI lo usan. Es el estándar de facto.

---

## 0. Alcance v2 — qué pidieron los revisores (scope lock)

Lo enviado a ASAID fue el paper de **medición** (efectos per-instrucción vía ordered logit). El
selective-reinforcement / BKT fue "el sistema que esto habilita" — propuesta, no el núcleo.

Feedback ASAID: **R1** = baselines más amplios + validación real · **R3** = negación en instrucciones
HDI>0 · **R2** = elogio. **Ninguno pide construir el BKT.** Todo es robustez de **medición**.

**Dos cosas bayesianas — no confundir:**
- **(A) Tracker BKT vivo** (`tracker.py`, GRM+Laplace, online) → alimenta `SelectiveReinforcement` (lazo cerrado).
- **(B) Ordered logit jerárquico** (`analyze.py`, PyMC, offline) → **el resultado del paper**. NO es BKT.

→ **v2 core = canal B (medición robusta).** El solver del benchmark **no necesita el tracker vivo**.
El BKT (A) queda como **mini-test/demostración**: se copia `tracker.py` sin tocar y corre SOLO en la
condición `selective`, como add-on chico. NO se sobre-ingenieriza ni es parte del dataset core.

---

## 1. Mapeo harness → Inspect

| Harness actual | Primitivo Inspect | Nota |
|---|---|---|
| `conversations/*_v3_*.json` (codebase, condition, planted_decisions, test_turns, turns[]) | `Sample(input, target, metadata)` | **1 conversación = 1 Sample** |
| `ConversationRunner.run()` (loop multi-turno, inject, tool loop) | `@solver` custom (async, loop sobre turns) | el crecimiento a ~200K vive acá |
| `checkers.py` (12 decision checkers + 5 base, deterministas) | `@scorer` custom envolviendo checkers (puros) | sin cambios a la lógica |
| `_judge_persona` / `_judge_safety` (juez LLM) | `get_model(role="judge_n")` ×3 + `asyncio.gather` (ver §3.4) | **panel cross-family ciego** |
| `tracker.py` (GRM + Laplace online) | inline en el solver **solo si `reinforcement=selective`** | BKT mini-demo (§0), no en el core |
| `reinforcer.py` (No/Uniform/Selective) | param del `@task` → branch en el solver | condición experimental |
| `providers.py` (Anthropic/OpenAI/OpenRouter/…) | model strings de Inspect (`azureai/…`, `openai/…`) | Inspect maneja los providers |
| `tool_executor` (write_file/read_file, files_read) | `@tool` Inspect + `state.store` para files_read | read-before-write se trackea en store |
| réplicas (fix de sesgo de estocasticidad) | `epochs=N` en `eval_set` | nativo |
| prompt caching (lever de costo) | `cache=True` en `GenerateConfig` | nativo |
| model ladder × condiciones (factorial) | `eval_set(tasks=[...], model=[...])` | nativo, con retry/dedup |
| `analyze.py` (ordered logit PyMC) | post-proceso sobre los `.eval` logs → df | reusar el código existente |

**Decisión estructural:** Sample = conversación, NO observación `(decisión,turno)`. Razón:
re-correr la conversación entera por observación desperdicia los ~200K de contexto. El solver
corre la trayectoria una vez; el scorer extrae los scores ordinales por `(decisión, test_turn)`
y los loguea. El modelo bayesiano corre después sobre el log (Inspect loguea todo).

---

## 2. Estructura del paquete

**Espejo exacto de `inspect_evals/makemesay`** (template oficial: port del make-me-say de OpenAI,
metodología DeepMind — multi-turno, solver+scorer custom, model-roles para 2 modelos). Misma
disposición de archivos:

```
eval/                              # nuevo paquete Inspect (reemplaza experiments/harness para el release)
  retention/
    __init__.py       # exporta el task:  from .retention import instruction_retention
    retention.py      # @task instruction_retention(condition, reinforcement, holdout=False) → Task(...)
    dataset.py        # (= utils.py de makemesay) JSONs → list[Sample] (metadata: codebase, condition, planted_decisions, test_turns, turns)
    solver.py         # @solver retention_harness — loop multi-turno + inject + reinforcement (tracker inline SOLO si selective)
    scorer.py         # deterministic_compliance() + judge_panel() + @metric κ/retención
    tools.py          # @tool write_file/read_file/search_code (files_read → state.store)
    prompts.py        # system prompts + plantillas de juez
    tracker.py        # (copia de harness/tracker.py — sin cambios de lógica)
    checkers.py       # (copia de harness/checkers.py — sin cambios de lógica)
    eval.yaml         # metadata del eval (convención makemesay: version, autores, refs)
    README.md         # cómo correr + cómo submittear a Inspect Evals
  run.py              # eval_set(tasks × candidate models × epochs, cache=True)
  analysis/           # post-proceso .eval → ordered logit (port de analyze.py)
  data/
    public/           # ~10 instrucciones plantadas de ejemplo (subset público)
    holdout/          # set completo (no se publica — anti-contaminación estilo Epoch)
```

### Convenciones reales extraídas de makemesay (a respetar)

- **Task**: `@task def instruction_retention(...) -> Task: return Task(dataset=, solver=, scorer=, version=, metadata=)`.
- **Solver**: `@solver` → `async def solve(state: TaskState, generate: Generate) -> TaskState`. Loop de turnos;
  `await get_model(role="candidate").generate(msgs)`; append a `state.messages` (crecimiento a 200K);
  `state.output = ModelOutput.from_message(...)`; stash de objetos ricos (outputs por turno, tracker final)
  en `state.metadata`/`state.store` para el scorer.
- **Scorer**: `@scorer(metrics=[...])` → `async def score(state, target) -> Score(value=, answer=, explanation=)`.
  Lee `state.metadata`/`store`. Jueces vía `get_model(role="judge_1"|...)` — **ciegos** (no se les pasa la
  instrucción plantada).
- **Métricas custom**: `@metric def name() -> Metric` tomando `list[SampleScore] -> float`. Acá van: retención
  por tipo de decisión, decaimiento por posición/turno, κ checker–juez e inter-juez.
- **Multi-modelo = model-roles** (NO hardcodear strings): roles `candidate`, `judge_1`, `judge_2`, `judge_3`.

---

## 3. Scorer design (el corazón del eval) — con evidencia de evals reales

### 3.1 Modelo de estado: store vs metadata (decidido por evidencia)

| Dónde | Qué | Por qué | Evidencia |
|---|---|---|---|
| `state.metadata` (frozen) | contexto inmutable per-sample: codebase, condition, planted_decisions, test_turns, turns[] | se fija al crear el Sample, el scorer lo lee, no muta | swe_bench `metadata[base_commit]`; agentdojo `pre_environment` |
| `state.store` | mutable entre turnos: `{test_turn: output}`, `files_read: set`, estado final del tracker | acumula durante el loop, el scorer lo recorre | **MASK** `store.set(PRESSURED_RESPONSES, ...)` → scorer mapea jueces sobre la lista = **nuestro patrón exacto** |

Tipado opcional: `class RetentionMeta(BaseModel, frozen=True)` + `state.metadata_as(RetentionMeta)`.

### 3.2 Sandbox: NO lo necesitamos (decisión por evidencia)

`agentdojo` hace read/write de archivos **sin sandbox** (FS simulado vía `store`). Sandbox solo
lo usan los evals que **ejecutan** código (swe_bench, bigcodebench, gdm_* → `sandbox().exec()`).
Nuestro caso: leemos el repo **read-only** y `write_file` se **captura para scoring, no se ejecuta**.
→ **Sin sandbox.** El `@tool` lee del disco / inyecta contenido y registra el intento de write en `store`.
Simplifica infra y baja costo. (El harness viejo ya nunca ejecuta nada — `_inject_context` solo lee.)

### 3.3 Score multi-punto = dict (patrón idiomático confirmado)

```python
@scorer(metrics=[retention_by_decision(), retention_by_turn(), mean(), stderr()])
def deterministic_compliance():
    async def score(state, target):
        outputs = state.store.get("turn_outputs")          # {test_turn: assistant_text}
        value = {}
        for turn, text in outputs.items():
            for decision_id in state.metadata["test_turns"][turn]:
                r = check_decision(decision_id, text)        # checkers.py sin tocar
                value[f"{decision_id}@{turn}"] = r.score     # 0-3
        return Score(value=value, metadata={"by_decision": ...})
    return score
```

- `Score.value` como **dict** = patrón de MASK / AIR-Bench / ANIMA / ape para multi-métrica en un scorer.
- **Métricas custom** desempaquetan el dict y agrupan: `retention_by_decision()` (por tipo),
  `retention_by_turn()` (decaimiento por posición). Patrón AIR-Bench `accuracy_by_category` (dict→dict)
  o built-in `grouped(mean(), group_key="decision_type")` (mind2web).

### 3.4 Panel de jueces (canal secundario)

- Cada juez vía `get_model(role="judge_1", default="azureai/grok-4.3")` — **rebindable** por CLI
  (`-M judge_1=...`) sin tocar código (patrón mask/anima/ipi).
- Panel en paralelo: `asyncio.gather(...)` (patrón ANIMA). **Corrección de blindness:** el juez de
  decision-compliance NECESITA ver la instrucción + el código para ratear → es ciego a
  **condición/modelo/veredicto-del-checker**, NO a la instrucción. (El "ciego a la instrucción" solo
  aplicaría a un juez de fuga/leak, que no es este canal.)
- **Per-judge va en `Score.value`, NO en metadata** (regla AISI BEST_PRACTICES): la epoch-aggregation
  reduce `value` pero no `metadata`; los scores de jueces son reducibles → keys tipo
  `judge_1@{decision}@{turn}` en el dict de `value`. `Score.metadata` solo para IDs no-reducibles
  (decision_type, task_id) y debug.

### 3.5 κ + calibración de jueces → OFFLINE en `analysis/`

κ no es nativo (healthbench usa solo "agreement + F1") → el acuerdo checker–juez e inter-juez
(Cohen/Fleiss) se computa post-eval sobre los `.eval` logs, junto al ordered-logit. Los scores
per-judge están en `Score.value` (§3.4) → datos crudos por epoch en el log.

**Calibración de jueces (AISI BEST_PRACTICES + tool CJE):** los jueces viven en su propia escala,
no la del oráculo; las barras de error no capturan miscalibración. **Nuestros checkers determinísticos
SON el oráculo.** Usamos `tools/judge_calibration_diagnostics.py` (CJE, isotonic) para aprender el mapeo
juez→checker con 50–100 labels y reportar estimaciones calibradas con CI. Ataca el self-bias de forma
rigurosa, más allá de κ.

Esto materializa el fix de sesgo #2 (validez de constructo, triangulación) y #3 (self-bias del juez).

---

## 4. Config de corrida (factorial v2)

**Dos ejes distintos — no confundir (ver §0):**
- **Eje de medición (CORE, canal B):** `condition ∈ {baseline, treatment}`. Es lo que mide el paisaje
  de retención y alimenta el ordered logit. Es el factorial principal de v2.
- **Eje de reforzamiento (BKT mini-demo, canal A):** `reinforcement ∈ {none, uniform, selective}`.
  Solo `selective` usa el tracker vivo. Corrida chica aparte (1–2 modelos), NO el factorial grande.

Convención makemesay: el **candidato** (modelo-bajo-test) es el `model` de la corrida; los **jueces**
van como `model-roles` fijos. Barremos la escalera de candidatos con el `model=[...]` de `eval_set`,
y los jueces quedan constantes vía `--model-roles`.

```python
# ---- CORE: factorial de medición (responde R1) ----
eval_set(
    tasks=[instruction_retention(condition=c) for c in ["baseline", "treatment"]],
    model=[  # candidatos: escalera cuota-alta (cap >> 1 en sub Sponsored), 4 labs, 20B→671B
        "azureai/gpt-oss-20b",     # OpenAI-OSS 21B MoE   (cap 1000)
        "azureai/qwen3-32b",       # Alibaba 32B          (cap 1000)
        "azureai/llama-3.3-70b",   # Meta 70B             (cap 10000)
        "azureai/gpt-oss-120b",    # OpenAI-OSS 117B MoE  (cap 1M)
        "azureai/DeepSeek-V3.2",   # DeepSeek 671B MoE    (cap 1M, SOTA coder)
    ],
    # cap=1 (Phi-4-mini, Mistral-*, Llama-3.1-8B) evitados: requieren quota request
    # en Foundry portal (Owner). Tier <10B y labs Mistral/Microsoft quedan afuera salvo cuota.
    model_roles={  # jueces fijos, disjuntos del test set (fix self-bias)
        "judge_1": "azureai/grok-4.3",          # xAI
        "judge_2": "azureai/kimi-k2.6",         # MoonshotAI
        "judge_3": "azureai/cohere-command-a",  # Cohere
    },
    log_dir="./logs/retention-v2",
    epochs=5,                       # réplicas (fix estocasticidad)
    config=GenerateConfig(temperature=0.2, cache=True),  # caching = lever de costo
    max_connections=10,
    retry_attempts=3,
)
```

El solver usa `get_model(role="candidate")` (default = el `model` de la corrida) y el scorer
`get_model(role="judge_n")`. Así el mismo task corre 6 candidatos sin tocar código.

```python
# ---- BKT mini-demo (canal A, opcional, chico) ----
eval_set(
    tasks=[instruction_retention(condition="treatment", reinforcement=r)
           for r in ["none", "uniform", "selective"]],   # selective → tracker vivo
    model=["azureai/qwen3-32b"],   # 1-2 modelos, no la escalera entera
    epochs=3,
    ...
)
```

Costo estimado total (core + mini-demo, con caching + ventana de juez ~10K): **~$250–350** sobre los $5k Sponsored.

---

## 5. Mismatches a resolver en implementación

1. **Tool loop / read-before-write:** `@tool write_file`/`read_file` que escriben `files_read` a
   `state.store` (patrón agentdojo `store().get("filesystem")`); el checker lo lee. Sin sandbox (§3.2).
2. **Tracker vivo + SelectiveReinforcement:** Selective necesita el ranking del tracker mid-conversación.
   El tracker es python puro y barato → se corre inline en el solver entre turnos. Sin cambios.
3. **Scoring multi-turno por Sample:** el solver guarda `{test_turn: output}` en `state.store`; el
   scorer los recorre y devuelve `Score.value` dict (§3.3). Soportado.
4. **⚠️ Gotcha epochs + dict-value:** el reducer **default (mean) ROMPE con `Score.value` dict**
   (MASK lo evita con `Epochs(1, _reduce())`). Pero nosotros SÍ queremos réplicas. Resolución:
   `Epochs(N, reducer_custom)` donde el reducer promedia key-a-key, **y** extraemos los scores
   crudos per-epoch del `.eval` log para el modelo bayesiano (cada epoch = una observación réplica).
   Reducers vistos: `max_score` (worst-case, persistbench), `at_least_1` (gdm), mean. Elegimos mean
   por-key para el headline; el bayesiano usa el crudo.
5. **Loop del solver:** dos patrones válidos — `for turn in turns` (makemesay, turnos scripted = nuestro caso)
   vs `while not state.completed` (gdm, agente abierto). Usamos **for sobre los turnos scripted**.
6. **Model strings Azure:** verificar en impl si Azure OpenAI usa `openai/<deployment>` (env `AZURE_OPENAI_*`)
   vs Foundry `azureai/<deployment>`. Ambos soportados; confirmar por modelo.

---

## 6. Plan de migración (incremental, con checkpoints)

- [x] **F0 — scaffold:** `eval/retention/` creado, tracker.py + checkers.py copiados verbatim, `inspect_ai 0.3.237` + pytest instalados.
- [x] **F1 — dataset.py:** loader JSON → 6 Samples (3 codebases × {baseline,treatment}); 4 tests verdes. (El ×3 de réplicas va por epochs, no por templates.)
- [x] **F2 — solver.py + tools.py:** port fiel de `_send_with_tool_loop` (version=3, NoReinforcement, inject_files, write_file solo en test_turns). Smoke test contra `mockllm` verde (26 turnos, 6 test-turns capturados). $0.
- [x] **F3 — scorers.py determinista:** `@scorer deterministic_compliance` + helper puro `score_turn_outputs`; `Score.value` dict `{decision@turn:0-3}`, métrica `compliance_mean`. Fidelidad probada (scorer == `check_decision` directo + valores conocidos). 8/8 tests verdes. Único cambio al verbatim: quitar el import `harness.providers.Message` de checkers.py (type-hint del checker v1, duck-typed).
- [x] **F4 — judge_panel:** 3 jueces vía `get_model(role="judge_n")`, `asyncio.gather`, prompts con instrucción canónica (`prompts.py`, 12 textos de la data), per-judge en `Score.value` (36 keys). Task con `scorer=[determinista, panel]`. Wiring probado con mockllm. (κ va offline en F7.)
- [x] **F5 — run.py + Azure:** recurso `tk-retention-eval` (AIServices, eastus) provisionado, phi-4-mini + gpt-4.1-mini deployados, provider `azureai` (inference unificado). Smoke real **success en 94s**: 12 det + 36 panel keys con scores reales. `run.py` artefacto F6. Costo real ~$0.5/conv full (~$90-300 factorial). **2 issues para F6:** phi cap=1 throttle (cuota), sin prefix-caching.
- [ ] **F6 — factorial completo:** 6 modelos × 3 condiciones × 5 epochs.
- [ ] **F7 — analysis:** port de analyze.py sobre los .eval logs → ordered logit + forest plot.
- [ ] **F8 — release:** README + subset público + decidir submit a Inspect Evals `/register/`.

**F3 = fidelidad metodológica, NO números iguales.** v2 corre modelos nuevos + jueces debiased +
réplicas → los números DEBEN diferir del harness viejo (qwen-only, self-bias); ese es el objetivo.
Lo que se preserva es el MÉTODO: checkers verbatim, escala 0-3, las 12 decisiones, scorear el texto
final del assistant en los test_turns. El test valida que el scorer da lo mismo que `check_decision`
directo sobre el mismo texto (unit-level), no que reproduzca corridas viejas. Esto hace los resultados
comparables en metodología con el paper, respetando lo que ya se hizo (alineado con AISI:
"matches the original evaluation's methodology").

---

## 7. Decisiones abiertas

1. ~~¿paquete nuevo vs in-place?~~ **DECIDIDO: paquete nuevo aislado** — es el estándar AISI
   (CONTRIBUTING §Isolated packages, ADR-0009) + el viejo queda como reference para la paridad F3
   (CONTRIBUTING:139,192). Versión del task `1-A` en `eval.yaml` (TASK_VERSIONING / ADR-0002).
2. **Wrinkle holdout:** nuestro set es CHICO (12 tipos de decisión × 3 codebases), no ~350 como
   FrontierMath. Holdear poco no tiene sentido y el riesgo de contaminación es bajo (mide estilo/compliance,
   no conocimiento). Opciones: (a) publicar todo + versionar tasks (estilo makemesay) y aceptar que es
   un eval de compliance, no de conocimiento secreto; (b) holdear codebases nuevas, no instrucciones.
   Probablemente (a). El split público/holdout de Epoch aplica menos acá.
3. ¿Submit a Inspect Evals oficial, o release propio en GitHub primero?
4. Lista final de modelos (¿agregar DeepSeek-V3.2 671B como techo, o reasoning como eje extra?).
