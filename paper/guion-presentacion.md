# Guion de presentación — *No Todas las Instrucciones se Olvidan Igual*

**55 JAIIO / ASAID 2026 · Tomás P. Korenblit (UNSAM)**
Duración objetivo: ~12 minutos de exposición + preguntas.

---

## Diapositiva 1 — Título (0:00–0:30)

Buenas, gracias. Voy a presentar *No Todas las Instrucciones se Olvidan Igual*,
un trabajo sobre cómo los modelos de lenguaje retienen —o dejan de retener—
las instrucciones que les damos en sesiones largas.

La idea en una frase: cuando le damos varias instrucciones a un agente LLM,
el modelo no las va olvidando todas por igual. Algunas las cumple siempre,
otras las abandona en silencio. Y medir cuál es cuál tiene consecuencias
prácticas, tanto de costo como de seguridad.

## Diapositiva 2 — El problema (0:30–2:00)

Los LLMs se usan cada vez más como agentes autónomos: corren en un loop,
llaman herramientas, y operan durante cientos de turnos. Las instrucciones que
gobiernan ese agente —límites operativos, barreras de seguridad— se dan una
sola vez, al principio, y tienen que sostenerse durante toda la sesión.

Pero sabemos que la adherencia a las instrucciones se degrada a medida que el
contexto crece; es lo que se conoce como *context rot*. Laban y colegas
midieron en 2025 una caída promedio de cumplimiento del 39% en 15 modelos en
escenarios multi-turno. La causa es arquitectural: la atención no se
distribuye de manera uniforme en la ventana de contexto —la famosa curva en U
de "lost in the middle"—, así que una instrucción dicha una vez y enterrada
bajo salida de herramientas compite en desventaja contra todo lo que viene
después.

Y acá está el punto clave: en un chat, si el modelo olvida una preferencia, el
usuario lo nota y la repite. En un agente desplegado no hay nadie mirando. Una
barrera de seguridad que decae, decae en silencio, mientras el agente sigue
actuando con herramientas cuyos efectos son reales y muchas veces
irreversibles.

## Diapositiva 3 — Qué falta en el trabajo previo (2:00–3:00)

El trabajo previo estableció que el cumplimiento cae, pero siempre reporta
promedios sobre conjuntos de instrucciones. Y las mitigaciones propuestas son
uniformes: recordatorios periódicos que repiten *todas* las instrucciones en
cada intervención.

Si la retención es heterogénea, el promedio esconde justo lo que una política
de refuerzo necesita saber. Una instrucción que ya se retiene no necesita
refuerzo, y una que empeora al repetirse no debería recibirlo. Nadie había
medido esto a nivel de instrucción individual. Eso es lo que hacemos.

La inspiración viene de educación: *Bayesian Knowledge Tracing*, que hace 30
años estima la probabilidad de que un estudiante domine cada concepto. Acá el
modelo es el estudiante y las instrucciones son los conceptos. Pero un sistema
así solo tiene sentido si la retención es efectivamente heterogénea — y eso es
la pregunta empírica de este paper.

## Diapositiva 4 — Método: el protocolo (3:00–5:00)

Simulamos un asistente de programación trabajando sobre un codebase real de
código abierto durante 25 turnos. En cada turno recibe un mensaje del usuario
y puede llamar herramientas. Entre los turnos 0 y 19 se inyectan archivos
reales del repositorio, lo que va acumulando presión de contexto.

En la condición de tratamiento, sembramos 12 preferencias de programación como
pedidos casuales dentro de los mensajes del usuario: seis temprano (turnos
1–7) y seis tarde (turnos 14–19). Cubren estilo de código, arquitectura,
testing, nombres, dependencias y documentación. Por ejemplo: "Importante:
para operaciones con arrays usá siempre broadcasting de NumPy en lugar de
for loops".

En la condición de base la conversación es idéntica —mismos archivos, misma
tarea— pero sin sembrar preferencias. Eso nos da lo que el modelo hace *por
defecto* para cada decisión.

En los turnos 20 a 25 pedimos tareas de generación de código diseñadas para
elicitar cada decisión, y evaluamos la salida con verificadores
determinísticos —regex y pattern matching, sin juez LLM— que dan un puntaje
ordinal de 0 (ignorada) a 3 (cumplida por completo). Al no haber LLM en el
loop de evaluación, los puntajes son reproducibles.

Corrimos esto en tres codebases del ecosistema bayesiano de Python, elegidos
para variar la presión de contexto: Bambi (~98K tokens al turno 20), ArviZ
(~160K) y PyMC (~203K). Y en cinco modelos; Qwen 3.5 fue el principal, con
base y tratamiento; los otros cuatro solo en tratamiento para verificar
generalización. En total: 28 conversaciones, 244 observaciones de
cumplimiento.

## Diapositiva 5 — Método: el modelo estadístico (5:00–6:30)

Modelamos los puntajes con una regresión logística ordinal —los intervalos
entre 0, 1, 2 y 3 no son iguales, así que un modelo lineal sería incorrecto—
con efectos jerárquicos por tipo de decisión.

Para cada observación, la variable latente es un intercepto α por decisión
—el cumplimiento sin que se lo pidan— más un efecto de tratamiento β por
decisión: cuánto mejora el cumplimiento por decirlo explícitamente. Ambos con
priors jerárquicos débilmente informativos.

El parámetro científico clave es σ_β: la desviación estándar grupal de los
efectos de tratamiento. Si σ_β es grande, las instrucciones responden
distinto a ser enunciadas — que es exactamente la premisa que el refuerzo
selectivo necesita.

Implementado en PyMC, muestreado con NUTS vía nutpie. Diagnósticos limpios:
cero divergencias, R-hat ≤ 1.01, ESS mínimo 1311, y los chequeos predictivos
posteriores reproducen la distribución observada.

## Diapositiva 6 — Resultado 1: la heterogeneidad es grande (6:30–8:00)

Primer resultado, el central: σ_β = 2.11, con intervalo de credibilidad del
94% entre 1.06 y 3.28. Los efectos individuales van de −2.4 a +5.4 en
log-odds — casi ocho unidades de rango. La retención es fuertemente
heterogénea.

El posterior separa los 12 tipos en tres grupos.

**Primero, las que se benefician de ser enunciadas.** Tres tipos tienen efecto
con HDI enteramente positivo. El caso extremo es `testing_parametrize`:
β = 5.44. Los modelos casi nunca usan `pytest.mark.parametrize` por su cuenta
—base 0.00— pero retienen la preferencia cuando se les dice —tratamiento
2.79. Lo mismo con constantes a nivel módulo y funciones standalone: base
cercana a cero, retención significativa al enunciarse.

**Segundo, las que no necesitan intervención.** Ocho tipos tienen HDI que
cruza cero. Varias tienen cumplimiento de base altísimo —broadcasting: 3.00,
docstrings estilo NumPy: 3.00—; el modelo ya sigue esas convenciones solo, y
repetírselas no cambia nada.

## Diapositiva 7 — Resultado 2: el efecto negativo marginal (8:00–9:00)

**Y tercero, un caso curioso:** `dependencies_no_new` —"no agregues imports
nuevos"— tiene el único efecto negativo del estudio: β = −2.36. La base es
2.25 —los modelos naturalmente evitan agregar imports— pero al pedirlo
explícitamente el puntaje *baja* a 0.77.

Dos aclaraciones importantes. Es marginal: el intervalo apenas excluye el
cero. Y es la única instrucción formulada como negación —todas las demás
dicen qué hacer, no qué evitar—, además de que el verificador cuenta como
nuevo cualquier import, incluso los ya presentes en el archivo. Así que lo
tratamos como candidato a artefacto de medición, no como daño robusto.
Distinguir si el problema es la negación o el contenido requiere comparar
"evitá imports nuevos" contra "usá solo los imports existentes" — eso queda
como trabajo futuro.

## Diapositiva 8 — Resultado 3: no es el modelo, es la instrucción (9:00–9:45)

Ajustamos también un modelo con interceptos por modelo y por codebase: ambas
desviaciones grupales quedaron cerca de cero. Dentro de la resolución de este
diseño, lo que determina si una instrucción se retiene es la instrucción
misma, no el modelo que la procesa ni cuánto contexto la rodea —de 98K a 203K
tokens.

Un dato que descarta una lectura tentadora: la retención no sube del modelo
de 26B al de 120B. O sea, esto no parece ser capacidad del modelo con otro
nombre. Un modelo más grande no es automáticamente más obediente.

Cautela: la condición de base viene de un solo modelo, así que hablamos de
invariancia dentro de nuestro diseño, no de ausencia demostrada de efectos de
modelo. La sensibilidad solo-Qwen replica la estructura con r = 0.80.

## Diapositiva 9 — El ranking de refuerzo (9:45–10:45)

Del posterior derivamos un ranking de prioridades: para cada decisión, el
cambio en la probabilidad de puntaje ≥ 2 al reforzarla.

De 12 tipos, solo 3 tienen ganancia con intervalo enteramente positivo.
Una política uniforme que refuerza las 12 gasta tokens en 8 instrucciones que
no necesitan ayuda y 1 con efecto negativo marginal. Es decir: el refuerzo
uniforme —la mitigación estándar— gasta la mayoría de sus tokens sin ganancia.

Y la lectura de seguridad es el espejo de esto: una barrera de seguridad es
una instrucción más. Las reglas que el modelo no seguiría por sí solo son
exactamente las más propensas a fallar. Como la seguridad es conjuntiva
—tienen que sostenerse *todas* las reglas—, una tasa agregada de cumplimiento
no puede decir si la regla que importa sigue vigente. Sin monitoreo por
instrucción, nada señala la falla.

## Diapositiva 10 — Limitaciones (10:45–11:30)

Las principales, brevemente:

- La base viene de un solo modelo; la sensibilidad mitiga pero no elimina.
- Sembramos preferencias de código, no guardrails reales. Son el mismo tipo
  de objeto compitiendo por la misma atención, pero el vínculo es una
  hipótesis fundada en el mecanismo, no un bypass demostrado.
- Medimos en los turnos 20–25: es una foto de retención, no una curva de
  olvido.
- Los verificadores tienen límites de validez de constructo; cuatro tipos
  tienen tasas altas de "sin señal clara", aunque los hallazgos principales
  no dependen de ese artefacto.
- Y este paper *no* implementa BKT: mide la heterogeneidad que haría útil a
  un sistema BKT.

## Diapositiva 11 — Conclusión (11:30–12:00)

En resumen: medimos retención por instrucción y encontramos efectos que
abarcan casi ocho unidades de log-odds, desde instrucciones que el modelo
adopta solo si se le dicen hasta otras que ya sigue por defecto. El patrón se
sostiene en cinco modelos y tres niveles de presión de contexto.

El resultado práctico es concreto: solo 3 de 12 instrucciones justifican el
refuerzo. Y las probabilidades de retención que estimamos acá son exactamente
el insumo que un sistema de Knowledge Tracing bayesiano necesitaría — construir
ese sistema es el paso siguiente.

Gracias. Quedo abierto a preguntas.

---

## Apéndice — Preguntas probables y respuestas cortas

**¿Por qué checkers determinísticos y no un juez LLM?**
Reproducibilidad: mismo output, mismo puntaje, en cualquier re-corrida. El
costo es validez de constructo, que reconocemos; el plan es complementar con
un panel ciego de jueces LLM de familias distintas a las evaluadas, reportando
acuerdo checker–juez e inter-juez.

**¿El efecto negativo no invalida el refuerzo?**
Es marginal (el HDI apenas excluye cero) y confundido con el verificador y con
la negación en el fraseo. Justamente por eso el ranking dice "evitar
(marginal)" y no una conclusión fuerte. El experimento que lo resuelve —variar
el marco de negación manteniendo el contenido— está diseñado como trabajo
futuro.

**¿Cómo sé que no es capacidad del modelo?**
La retención no aumenta de 26B a 120B parámetros. Si fuera capacidad,
esperaríamos monotonía con el tamaño.

**¿244 observaciones no es poco?**
Para algunas celdas sí (mínimo 4), y el modelo jerárquico lo maneja con
pooling parcial: las decisiones con pocos datos tienen intervalos anchos que
reflejan esa incertidumbre. La categoría "incierta" del ranking es
explícitamente preliminar. LOO no muestra observaciones problemáticas
(todos los k̂ de Pareto < 0.7).

**¿Esto aplica fuera de código Python?**
No lo sabemos: toda la evidencia es de sesiones de programación en Python.
Que la misma estructura por instrucción valga para agentes de uso de
herramientas bajo restricciones de seguridad en otros dominios es exactamente
el experimento que este paper motiva pero no corre.
