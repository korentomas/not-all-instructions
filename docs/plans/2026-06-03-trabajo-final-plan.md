# Plan — Trabajo Final Individual (Ciencia de Datos 1C2026)

**Autor:** Tomás Pablo Korenblit
**Formato:** Times New Roman 12, interlineado 1,5, márgenes normales, 6–8 páginas.
**Idioma:** español rioplatense (voseo), registro académico.
**Presupuesto de palabras:** ~3.000–3.800 (≈ 7 páginas).

> Estrategia central: el nodo es **Context Rot** (los LLMs pierden adherencia a
> instrucciones en conversaciones largas). La *propuesta de solución* no es
> especulativa: es mi estudio empírico ya realizado (el paper enviado a JAIIO
> 55) que mide la **heterogeneidad de retención por tipo de instrucción**, más
> el sistema de **refuerzo selectivo vía Bayesian Knowledge Tracing (BKT)** que
> ese hallazgo habilita. Esto da una propuesta que se *deriva lógicamente* del
> análisis, que es exactamente lo que pide la consigna.

---

## Arco argumental (una sola línea por sección)

1. El problema existe y es medible → **Context Rot**, caída de hasta 39%.
2. Es arquitectónico, no un bug → atención finita, curva U, saturación.
3. Importa por dos razones → **costo** (tokens) y **seguridad** (guardrails decaen sin alarma).
4. Lo que se hizo → medir el promedio, o mitigar de forma **uniforme**.
5. La brecha → **nadie desagrega por tipo de instrucción**; el promedio esconde la estructura.
6. Mi aporte → medí esa heterogeneidad (σ_β = 2,11): existe y es grande.
7. La solución que habilita → **refuerzo selectivo bayesiano (BKT) bajo presupuesto de tokens**.

---

## 1. Título  (~1 línea)

Debe nombrar tema **y** problema específico. Candidatos:

- **"No todas las instrucciones se olvidan igual: medición de la retención por
  tipo de instrucción en asistentes de programación con LLMs"** ← recomendado
  (traduce el título del paper; nombra tema = Context Rot, problema = heterogeneidad).
- Alternativa: *"Context Rot bajo presupuesto: refuerzo selectivo de
  instrucciones en LLMs mediante inferencia bayesiana."*

## 2. Resumen  (150–200 palabras)

Síntesis en un párrafo: tema (Context Rot), problema (las instrucciones decaen
y no sabemos si lo hacen de forma pareja), enfoque (revisión crítica de
medición + mecanismo + mitigaciones; estudio empírico bayesiano propio),
propuesta (refuerzo selectivo vía BKT), conclusión principal (la heterogeneidad
existe: 3 de 12 instrucciones se benefician del refuerzo, 1 empeora, 8 no lo
necesitan → el refuerzo uniforme malgasta presupuesto). Adaptar del abstract
español del paper (`paper/paper.tex`, líneas 57–73) recortando a ~180 palabras.

## 3. Introducción  (~0,75 pág, ~400 palabras)

Responde: ¿de qué trata?, ¿por qué importa?, ¿qué interés actual tiene?

- Área temática: LLMs e instruction following; el salto de los Transformers y
  RLHF que sacó a los LLMs del laboratorio (ChatGPT, 100M usuarios en 2 meses).
- Relevancia en Ciencia de Datos: evaluación de modelos, inferencia bayesiana
  aplicada, medición rigurosa de comportamiento.
- Actualidad: la ventana de contexto pasó de 16K tokens (2023) a 1M (2026); el
  campo recién en 2024–25 empieza a estudiar conversaciones largas. ~115.000
  papers/año en arXiv → imposible cubrir todo, selección pertinente.
- Cierre: anticipar el hallazgo (la retención varía > 1 orden de magnitud).

Fuentes: `guion-instancia2.md` SLIDES 3–8; `paper.tex` §Introduction.

## 4. Contexto y definición del problema  (~0,75 pág, ~400 palabras)

Delimitar el problema concreto y formular **la pregunta**.

- Definición de Context Rot: pérdida de adherencia a instrucciones a medida que
  crece la conversación, incluso con el system prompt estable.
- Por qué es desafío: la atención es un recurso finito que se reparte entre
  todos los tokens; las instrucciones del principio compiten con todo lo que se
  acumula después. Las del system prompt (posición 0) tienen ventaja; las
  preferencias del usuario inyectadas a mitad de charla, no.
- A quién/qué afecta: (a) **costo** — repetir todo el prompt cada turno
  multiplica el gasto a escala de miles de millones de tokens/día; (b)
  **seguridad** — los guardrails son instrucciones como cualquier otra; si
  decaen, el sistema falla en silencio.
- **Pregunta concreta que organiza el trabajo:** *¿decaen todas las
  instrucciones por igual, o la retención es heterogénea por tipo de
  instrucción?* (De la respuesta depende si tiene sentido reforzar de forma
  selectiva en lugar de uniforme.)

Fuentes: `guion.md` SLIDES 6, 8, 12; `guion-instancia2.md` SLIDES 2, 4, 13.

## 5. Revisión de la literatura  (~1,5 pág, ~750 palabras) — sección más larga

NO una lista de resúmenes aislados. Organizar por **función en el argumento**,
explicando por qué cada grupo es relevante para el problema. Cuatro bloques:

**(a) Medición de la degradación.**
- Laban et al. 2025 (Microsoft/Salesforce): −39% single→multi-turn, 15 modelos.
  Dato clave: la aptitud baja 16%, la **varianza sube 112%** → la inestabilidad
  es lo que explota (engancha con el marco bayesiano).
- He et al. 2024 (Meta, Multi-IF): *Instruction Forgetting Ratio*; o1-preview
  87,7%→70,7% en 3 turnos.
- Du et al. 2025: agrandar la ventana **no** resuelve la degradación.
- Punto común: todos reportan **promedios**; ninguno desagrega por instrucción.

**(b) Mecanismo: posición y saturación.**
- Liu et al. 2024 (TACL): curva U / "Lost in the Middle"; el medio se pierde.
  (Honestidad: el paper no mide atención directamente; la conexión posición-0 ↔
  system prompt es extrapolación mía.)
- Mu et al. 2025 (Berkeley): de 1 a 20 guardrails → adherencia individual → 0.
  Producción real (GPT Store) promedia 5,1 guardrails: ya cerca de la zona mala.

**(c) Encuadre de seguridad.**
- Anil et al. 2024 (Anthropic, NeurIPS): *many-shot jailbreaking*, la tasa de
  jailbreak sube con la longitud del contexto.
- Rivasseau 2025: formalización teórica (ratio system-prompt/contexto → 0);
  propone interrupciones periódicas, sin evaluación empírica.

**(d) Modelos bayesianos del comportamiento LLM.**
- Zhang, Yang & Wang 2025: los LLMs se comportan como **filtros bayesianos
  descontados** (γ < 1); el prior pierde peso frente a lo reciente. (Probado en
  belief-updating, no en instrucciones; el puente con compliance lo hago yo.)
- Corbett & Anderson 1994: **Bayesian Knowledge Tracing**, 30 años en
  educación; estima maestría por concepto turno a turno.

Fuentes: `guion-instancia2.md` SLIDES 9–13, 19; `paper.tex` §Related work.

## 6. Comparación de enfoques  (~1 pág, ~550 palabras)

Análisis crítico, no descriptivo. Eje: **qué resuelve / qué supone / qué cuesta
/ cuándo conviene**. Conviene una **tabla comparativa** de las 4 mitigaciones:

| Enfoque | Qué hace | Costo | Límite |
|---|---|---|---|
| Repetir prompt c/turno | Re-inyecta todo | N× tokens del system prompt | Mu: más reglas pueden empeorar |
| Jerarquía de instrucciones (Wallace 2024, OpenAI) | Prioriza por origen (system>user>tool) | Reentrenamiento | Ordena roles, no instrucciones; estático, no aborda decay temporal; over-refusal |
| Duplicación de prompt (Leviathan 2025, Google) | Repite el prompt back-to-back | 2× input tokens | Uniforme: duplica todo por igual |
| Recordatorios periódicos (Dongre 2025, Adobe/UIUC) | Re-inyecta el objetivo en t fijos | Tokens de reminder | Calendario fijo, no adaptativo; no decide *qué* reinyectar |

Argumento de cierre de la sección (el puente): **las cuatro estrategias son
uniformes** — tratan al conjunto de instrucciones como un solo bloque. Ninguna
es adaptativa; ninguna decide *qué* reforzar ni *cuándo*. Eso solo se
justificaría si todas las instrucciones decayeran igual — supuesto que **nadie
verificó**.

Fuentes: `guion-instancia2.md` SLIDES 14–18; `guion.md` SLIDE 13.

## 7. Limitaciones de los enfoques actuales  (~0,75 pág, ~400 palabras) — bisagra

Sección central: puente entre la crítica y mi propuesta. Identificar qué NO
está resuelto:

- **Métrica agregada esconde estructura.** Todos reportan compliance media; si
  cada instrucción decae distinto, el promedio oculta lo que importa. Una
  instrucción ya retenida no necesita refuerzo; una que empeora con la
  repetición no debería recibirlo.
- **Mitigaciones uniformes ⇒ presupuesto malgastado.** Reforzar todo por igual
  gasta tokens en instrucciones que no lo necesitan.
- **Seguridad sin medición primaria.** Las big-tech (Anthropic, OpenAI, Google,
  Meta) no publicaron investigación primaria sobre Context Rot por tipo de
  instrucción; las mitigaciones son uniformes porque no tienen datos para
  discriminar.
- **Falta de medición por instrucción ⇒ cualquier política de refuerzo
  selectivo es injustificada.** Sin ese dato, un sistema BKT sería especulación.

→ La brecha precisa: *nadie midió si el decay varía según el tipo de
instrucción.* Eso es lo que mi trabajo llena.

Fuentes: `guion-instancia2.md` SLIDE 19; `paper.tex` §Intro/§Discussion.

## 8. Propuesta de solución  (~1,25 pág, ~650 palabras) — mi aporte

Dos movimientos: **(8a) verificar el supuesto** (estudio empírico hecho) y
**(8b) el sistema que ese resultado habilita** (BKT selectivo).

**8a — Estudio empírico (prerrequisito).**
- Diseño: simulé un asistente de programación sobre 3 codebases reales (Bambi
  ~10K, ArviZ ~25K, PyMC ~57K líneas), 25 turnos, inyectando archivos reales
  para crear presión de contexto (98K–203K tokens al turno 20). 12 preferencias
  de programación plantadas como pedidos casuales del usuario (6 temprano, 6
  tarde). Condiciones baseline (sin plantar) vs treatment.
- Medición: checkers determinísticos (regex/pattern-matching, sin LLM-juez),
  score ordinal 0–3. Reproducible.
- Modelo: regresión **logística ordinal bayesiana** con efectos jerárquicos por
  tipo de decisión (PyMC, NUTS/nutpie). Parámetro clave: **σ_β**, desvío
  estándar grupal de los efectos de tratamiento — mide la heterogeneidad.
- Datos: 28 conversaciones, **244 observaciones**, 5 modelos (Qwen 3.5-27B
  primario + Gemini 3.1 Flash Lite, GPT-5.4-nano, Nemotron 3 Super 120B, Gemma
  4), 12 tipos de decisión, 3 codebases.

**Resultados (presentar como hallazgo, ver sección "Qué encontré" abajo):**
- **σ_β = 2,11** (HDI 94%: [1,06, 3,28]) → la heterogeneidad existe y es grande;
  efectos de −2,36 a +5,44 en log-odds.
- 3/12 se benefician del refuerzo (parametrize, module_constants, standalone),
  1 **empeora** (`deps_no_new`, β = −2,36 — única instrucción en negación), 8 no
  necesitan intervención (ya las cumple por defecto).
- Ni la arquitectura del modelo ni el tamaño del codebase explican varianza: lo
  que decide la retención es **la instrucción en sí**.
- Robustez: r = 0,80 entre el modelo completo y el restringido a Qwen.

**8b — El sistema habilitado: refuerzo selectivo vía BKT.**
- Inversión conceptual: el "estudiante" es el LLM; los "conceptos" son sus
  instrucciones. Se mantiene un posterior P(compliance) por instrucción, se
  actualiza con cada observación, y decae entre turnos (γ < 1).
- Política: con presupuesto fijo de B tokens, reforzar solo las instrucciones
  con menor probabilidad de compliance (y nunca las que empeoran con el
  refuerzo, p. ej. negaciones).
- Por qué se deriva del análisis: la heterogeneidad medida es **exactamente** el
  input que un sistema BKT necesita para ser útil. Sin σ_β grande, BKT colapsa a
  la política uniforme.

Fuentes: `paper.tex` §Method/§Setup/§Results; `guion-instancia2.md` SLIDE 20;
`guion.md` SLIDES 16–18; `experiments/config.yaml`.

## 9. Conclusiones  (~0,5 pág, ~280 palabras)

Recuperar: qué problema (Context Rot / heterogeneidad), qué mostró la revisión
(medición + mecanismo, pero todo agregado y uniforme), qué limitación (nadie
mide por instrucción), cuál es el aporte (medí que la retención varía > 1 orden
de magnitud; 3 benefician, 1 empeora, 8 neutras; consistente en 5 arquitecturas
y 3 niveles de presión de contexto). Implicancia práctica: el refuerzo uniforme
malgasta la mayor parte del presupuesto de tokens.

**Líneas futuras:** (1) medición temporal densa → curvas de olvido por
instrucción (estimar γ); (2) evaluación closed-loop del sistema BKT vs uniforme;
(3) análisis de negación (¿por qué "no agregues imports" empeora?).

Fuentes: `paper.tex` §Conclusion/§Future work.

## 10. Referencias  (formato APA 7)

Extraer de `paper/references.bib` (ya en biblatex APA). Citas mínimas a incluir:
Laban et al. 2025 · He et al. 2024 · Du et al. 2025 · Liu et al. 2024 · Mu et
al. 2025 · Anil et al. 2024 · Rivasseau 2025 · Wallace et al. 2024 · Leviathan
et al. 2025 · Dongre et al. 2025 · Zhang, Yang & Wang 2025 · Corbett & Anderson
1994 · Vaswani et al. 2017 · Brown et al. 2020 · Ouyang et al. 2022. Convertir
de biblatex a APA manual si se entrega en Word/Docs.

---

## Notas de producción

- **Reusar prosa existente:** el paper (`paper.tex`) ya tiene introducción,
  related work, método y discusión en inglés de calidad postdoc; traducir y
  comprimir a voseo en lugar de reescribir de cero.
- **Lo que NO meter:** METR/reward hacking (modo de falla paralelo, no Context
  Rot); detalle matemático del modelo ordinal (mencionar, no derivar).
- **Honestidad académica:** marcar explícitamente extrapolaciones propias (Liu
  ↔ atención; Zhang ↔ compliance) y que el paper está *bajo revisión* en JAIIO
  55, no validado por pares aún.
- **Figuras candidatas** (si el formato lo permite, máx 1–2): forest plot de
  efectos de tratamiento (`treatment_effects_forest.png`) y/o tabla de
  prioridades de refuerzo. Refuerzan "qué encontré" sin gastar páginas en prosa.
