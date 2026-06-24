# No todas las instrucciones se olvidan igual
### Medición de la retención por tipo de instrucción en asistentes de programación con LLMs

*Borrador v1 — Trabajo Final Individual, Ciencia de Datos 1C2026 — Tomás Pablo Korenblit*

> Versión básica. Énfasis en el diseño del experimento y el harness. Los números
> son aproximados y se afinan en la versión final contra `analysis/`.

---

## Resumen

Los modelos de lenguaje grandes (LLMs) pierden adherencia a las instrucciones a
medida que la conversación crece, un fenómeno conocido como *Context Rot*. La
literatura mide este olvido pero siempre de forma agregada: reporta una caída
promedio de compliance sobre todas las instrucciones juntas. Este trabajo
pregunta algo que nadie midió: ¿decaen todas las instrucciones por igual, o hay
unas que se retienen y otras que no? Para responderlo armé un harness que simula
un asistente de programación trabajando sobre codebases reales durante decenas
de turnos, planta 12 preferencias de código como pedidos casuales del usuario, y
mide con verificadores determinísticos si el modelo las sigue al final de la
conversación. Sobre esos datos ajusté un modelo bayesiano jerárquico. El
resultado es que la retención es fuertemente heterogénea: algunas instrucciones
se cumplen apenas se piden, la mayoría ya se cumplen por defecto, y al menos una
empeora cuando se la refuerza. Esa heterogeneidad es el prerrequisito empírico
de cualquier sistema de refuerzo selectivo: si todas decayeran igual, reforzar
selectivamente no tendría sentido.

---

## 1. Introducción

Cuando uno usa un asistente como ChatGPT o Claude, al principio funciona bien:
le explicás tu proyecto, le pedís que siga ciertas reglas, y obedece. Pero a
medida que la conversación se alarga, en algún momento deja de respetar lo que
le pediste. Sigue respondiendo, pero como si nunca le hubieras dicho nada. A ese
fenómeno se lo llama *Context Rot*.

No es un bug de un modelo puntual: le pasa a todos, y la causa es
arquitectónica. Un LLM, para generar cada palabra, decide a qué parte del
contexto prestarle atención. Esa atención es un recurso finito que se reparte
entre todos los tokens. Cuando el contexto es corto, sobra. Cuando crece —y hoy
las ventanas de contexto pasaron de 16 mil tokens en 2023 a un millón en
2026— las instrucciones del principio tienen que competir por atención con todo
lo que se fue acumulando después.

Esto importa por dos razones concretas. La primera es plata: la práctica más
común para mitigar el olvido es repetir todas las instrucciones en cada turno,
lo que multiplica el costo en tokens a escala de miles de millones por día. La
segunda es seguridad: los *guardrails* —las reglas que evitan que el modelo
haga algo dañino— son instrucciones como cualquier otra. Si decaen, el sistema
no tira ningún error: simplemente falla en silencio y no te enterás.

Este trabajo se ubica en la intersección de tres temas centrales de la Ciencia
de Datos: la evaluación rigurosa del comportamiento de modelos, el diseño
experimental con condiciones controladas, y la inferencia bayesiana jerárquica.

## 2. Contexto y definición del problema

El problema específico que organiza este trabajo no es *si* los LLMs olvidan
—eso ya está medido— sino *cómo* olvidan. Toda la literatura existente reporta
métricas agregadas: una compliance media que baja de tanto a tanto. Pero un
promedio esconde su estructura interna. Si cada instrucción decae a un ritmo
distinto, el promedio mezcla instrucciones que el modelo retiene perfectamente
con otras que ignora por completo.

Esa distinción no es cosmética, es lo que decide qué estrategia de mitigación
tiene sentido. Una instrucción que el modelo ya cumple no necesita que se la
recuerden. Una instrucción que empeora cuando se la repite no debería recibir
refuerzo nunca. Sin saber a qué tipo pertenece cada instrucción, cualquier
política de refuerzo está disparando a ciegas.

De ahí la **pregunta concreta**: ¿la retención de instrucciones es homogénea o
heterogénea entre tipos de instrucción? Si fuera homogénea, reforzar todo por
igual estaría justificado. Si fuera heterogénea, habría que reforzar de forma
selectiva —y para eso primero hay que medir esa heterogeneidad.

## 3. Revisión de la literatura

**Medición del olvido.** Laban et al. (2025) compararon el mismo modelo
recibiendo toda la información de una vez versus fragmentada en turnos, sobre 15
modelos: la compliance cae ~39% en el segundo caso. Un detalle clave es que la
*capacidad* del modelo baja poco (~16%); lo que explota es la *varianza* (+112%).
He et al. (2024), en Meta, definieron el *Instruction Forgetting Ratio* y
mostraron que la precisión cae de ~88% a ~71% en apenas tres turnos. Todos estos
trabajos reportan promedios; ninguno desagrega por tipo de instrucción.

**Mecanismo.** Liu et al. (2024) descubrieron la curva U ("Lost in the
Middle"): lo que está al principio y al final del contexto se atiende mejor que
lo del medio. Mu et al. (2025) mostraron un efecto distinto, de saturación: al
pasar de 1 a 20 reglas en el system prompt, la adherencia a cada una se acerca a
cero. Uno es problema de posición; el otro, de cantidad.

**Seguridad.** Anil et al. (2024, Anthropic) midieron que la tasa de jailbreak
sube con el largo del contexto (*many-shot jailbreaking*). Rivasseau (2025) lo
formalizó: el ratio de tokens del system prompt sobre el contexto total tiende a
cero.

**Marco bayesiano.** Zhang, Yang y Wang (2025) mostraron que los LLMs se
comportan como filtros bayesianos descontados (γ < 1): el prior pierde peso
frente a lo reciente. Y en educación, el *Bayesian Knowledge Tracing* (Corbett y
Anderson, 1994) lleva 30 años estimando, turno a turno, la probabilidad de que
un estudiante domine un concepto. La inversión conceptual que propongo es tratar
al LLM como el "estudiante" y a sus instrucciones como los "conceptos".

## 4. Comparación de enfoques

Las estrategias actuales para mantener compliance se pueden agrupar en cuatro, y
todas comparten un mismo límite:

| Enfoque | Idea | Costo | Límite |
|---|---|---|---|
| Repetir el prompt | Re-inyectar todo cada turno | N× tokens | Más reglas pueden empeorar (Mu) |
| Jerarquía de instrucciones (Wallace 2024) | Priorizar por origen en el training | Reentrenamiento | Ordena roles, no instrucciones; estática |
| Duplicar el prompt (Leviathan 2025) | Repetir la query back-to-back | 2× input | Duplica todo por igual |
| Recordatorios fijos (Dongre 2025) | Re-inyectar el objetivo en turnos fijos | tokens de reminder | Calendario fijo, no adaptativo |

El patrón es claro: las cuatro son **uniformes**. Tratan al conjunto de
instrucciones como un solo bloque y refuerzan todo por igual. Ninguna decide
*qué* reforzar ni *cuándo*. Eso solo estaría justificado si todas las
instrucciones decayeran igual —supuesto que, como vimos, nadie verificó.

## 5. Limitaciones de los enfoques actuales

El hueco es preciso: **nadie midió si el decay varía según el tipo de
instrucción.** De ahí se desprenden las limitaciones de lo existente:

- La métrica agregada esconde la estructura que importa para decidir qué hacer.
- Reforzar de forma uniforme malgasta presupuesto en instrucciones que no lo
  necesitan, y puede ser contraproducente en las que empeoran con la repetición.
- Las grandes empresas (Anthropic, OpenAI, Google, Meta) no publicaron
  investigación primaria sobre Context Rot por tipo de instrucción. Las
  mitigaciones son uniformes justamente porque no tienen datos para discriminar.

Esta limitación es la bisagra del trabajo: sin una medición por instrucción,
cualquier sistema de refuerzo selectivo sería pura especulación. Por eso, antes
de proponer el sistema, había que producir esa medición.

## 6. Propuesta de solución

La propuesta tiene dos partes: **(a)** un estudio empírico que verifica el
supuesto, y **(b)** el sistema de refuerzo selectivo que ese resultado habilita.
El grueso del trabajo —y donde está el aporte metodológico— es el harness
experimental.

### 6.1 El harness: cómo medí la retención

El desafío de diseño es que para medir si una instrucción se olvida hay que
crear una conversación realista, larga, con presión de contexto creciente, y al
final preguntarle al modelo algo que revele si todavía sigue lo que se le
pidió treinta mensajes atrás. Armé un harness en Python que hace exactamente
eso. Sus piezas:

**Codebases reales como fuente de presión.** En vez de rellenar el contexto con
texto sintético, el harness trabaja sobre tres librerías reales del ecosistema
bayesiano de Python, elegidas por tamaño creciente: Bambi (~10K líneas), ArviZ
(~25K) y PyMC (~57K). Durante los primeros ~20 turnos, el harness inyecta
archivos de código fuente reales de esas librerías en la conversación. Cada
archivo se trunca a ~40K caracteres para no desbordar la ventana, pero se
preserva el gradiente de presión: Bambi llega a ~98K tokens de contexto, PyMC a
~203K. Así, el mismo experimento se corre bajo tres niveles de presión.

**Plantado de decisiones.** Defino 12 "decisiones" de programación —preferencias
de estilo, arquitectura, testing, naming, dependencias y documentación. En la
condición *treatment*, estas 12 preferencias se plantan como pedidos casuales,
en línea, dentro de los mensajes del usuario (seis temprano, en los turnos 1–7;
seis tarde, en los 14–19). Por ejemplo: *"Importante: cuando escribas
operaciones con arrays en este proyecto, usá siempre broadcasting de numpy en
vez de for loops."* No son reglas del system prompt: son preferencias del
usuario inyectadas a mitad de charla, que es justamente el caso difícil (no
tienen la ventaja posicional del system prompt). En la condición *baseline*, la
conversación es idéntica —mismos archivos, misma tarea— pero sin plantar nada.
Eso permite medir qué hace el modelo por defecto, sin que se lo pidan.

**Turnos de evaluación.** En los turnos 20–25, el usuario pide tareas de
generación de código diseñadas para forzar cada decisión. Cada turno de test
evalúa exactamente dos decisiones (una plantada temprano y una tarde), para
medir tanto el olvido reciente como el de largo plazo.

**Verificadores determinísticos.** Acá está el corazón de la reproducibilidad.
Cada una de las 12 decisiones se evalúa con un *checker* que parsea el código
generado con expresiones regulares y pattern matching, y produce un puntaje
ordinal de 0 a 3 (0 = ignorada, 3 = cumplida del todo). No hay ningún
LLM-juez en el lazo de scoring: el resultado es 100% reproducible entre corridas.
Por ejemplo, el checker de `testing_parametrize` busca el decorador
`@pytest.mark.parametrize` y penaliza funciones de test separadas; el de
`broadcasting` detecta `for` loops versus operaciones de numpy; el de
`no_new_imports` cuenta sentencias `import` en el código generado.

**Lazo de herramientas y multi-proveedor.** El runner maneja un lazo de tool
calls: el modelo puede pedir leer archivos, buscar en el código o escribir
(`write_file`), y el harness ejecuta esas llamadas y devuelve resultados, hasta
un máximo de rondas por turno. Todo corre sobre una capa de proveedores
intercambiable, que me dejó evaluar cinco modelos (Qwen 3.5-27B como principal,
más Gemini, GPT-5-nano, Nemotron 120B y Gemma) vía OpenRouter y la API de
OpenAI, con reintentos y backoff ante errores de red.

El harness se construyó en tres iteraciones: v1 (asistente de Q&A genérico), v2
(asistente de programación con checkers determinísticos de formato, persona,
etc.), y v3 (la versión final, que agrega el plantado y la evaluación de las 12
decisiones). En total, el dataset final son 28 conversaciones y ~244
observaciones de compliance.

### 6.2 El análisis bayesiano

Sobre esas observaciones ordinales ajusté una **regresión logística ordinal**
(modelo de enlace acumulativo) con **efectos jerárquicos por tipo de decisión**.
El ordinal es la elección correcta porque la escala 0–3 no tiene intervalos
iguales: el salto de "ignorada" a "mínima" no es el mismo que de "casi" a
"completa". Para cada observación, la compliance latente depende de un intercepto
por decisión (lo que el modelo hace sin que le digan) más un efecto de
tratamiento por decisión (cuánto mejora al pedírselo).

El parámetro científicamente importante es **σ_β**: el desvío estándar grupal de
los efectos de tratamiento. Un σ_β grande significa que distintas instrucciones
responden muy distinto a que se las pida —es decir, heterogeneidad, que es
exactamente lo que hace falta para justificar el refuerzo selectivo. El modelo
se ajustó en PyMC con NUTS, con priors débilmente informativos y chequeos
predictivos previos y posteriores.

### 6.3 El sistema que esto habilita

El estudio es el prerrequisito de un sistema de refuerzo selectivo basado en
Bayesian Knowledge Tracing. En el harness ya está prototipado un *tracker*
bayesiano (`tracker.py`) que mantiene una creencia gaussiana N(μ, σ²) sobre la
compliance latente de cada instrucción, la actualiza con cada observación
mediante una aproximación de Laplace sobre un Graded Response Model, y la hace
decaer entre turnos (factor γ < 1) para modelar el olvido. Sobre eso corren tres
estrategias (`reinforcer.py`): no reforzar, reforzar todo de forma uniforme, o
reforzar **selectivamente** solo las instrucciones con menor probabilidad de
compliance, hasta agotar un presupuesto fijo de tokens. La política selectiva es
la que el estudio empírico justifica.

## 7. Conclusiones

Medí la retención de instrucciones por tipo en asistentes de programación y
encontré que es fuertemente heterogénea: algunas preferencias se retienen apenas
se las pide, la mayoría ya se cumplen por defecto (reforzarlas es desperdiciar
tokens), y al menos una empeora activamente cuando se la refuerza —llamativamente,
la única que está formulada como negación ("no agregues imports nuevos"). Esa
heterogeneidad se mantiene a través de cinco arquitecturas de modelo y tres
niveles de presión de contexto: lo que decide si una instrucción se retiene es
la instrucción misma, no el modelo ni el tamaño del codebase.

La implicancia práctica es directa: el refuerzo uniforme malgasta la mayor parte
de su presupuesto, y puede ser contraproducente. Una política derivada de la
medición puede decir qué reforzar, qué dejar tranquilo y qué no tocar nunca. Las
probabilidades de retención por instrucción que estimé son justamente el input
que un sistema de Bayesian Knowledge Tracing necesitaría para funcionar.

**Líneas futuras:** (1) medición temporal densa, puntuando compliance en cada
turno para ajustar curvas de olvido por instrucción y estimar γ; (2) evaluación
en lazo cerrado del sistema selectivo contra el uniforme; (3) análisis de
negación, para entender por qué decirle al modelo qué *no* hacer puede ser
contraproducente.

## 10. Referencias

*(A completar en formato APA 7 desde `paper/references.bib`.)* Laban et al.
(2025); He et al. (2024); Liu et al. (2024); Mu et al. (2025); Anil et al.
(2024); Rivasseau (2025); Wallace et al. (2024); Leviathan et al. (2025); Dongre
et al. (2025); Zhang, Yang y Wang (2025); Corbett y Anderson (1994); Vaswani et
al. (2017); Brown et al. (2020); Ouyang et al. (2022).
