# Guión — Instancia II
## "Análisis de soluciones existentes: Context Rot en LLMs"
### Tomás Pablo Korenblit — Ciencia de Datos 1C2026

Tiempo objetivo: 15:00. Audiencia: compañeros y profes — algunos saben de transformers, otros no.

---

## SLIDE 1 — Título (12s)

Buen día. Voy a hacer la revisión de literatura de mi nodo. El tema es Context Rot en modelos de lenguaje grandes, los LLMs como ChatGPT o Claude.

---

## SLIDE 2 — Delimitación (25s)

Cuando chateás con un modelo, al principio funciona bien. Le pedís que siga ciertas reglas y obedece. Pero a medida que la conversación crece, en algún momento se olvida. Sigue respondiéndote, pero deja de respetar lo que le pediste. A ese fenómeno lo llamamos Context Rot: los LLMs pierden adherencia a las instrucciones a medida que la conversación crece.

---

## SLIDE 3 — Explosión de papers en arXiv (35s)

Primero, una mirada al campo. Este gráfico muestra cuántos papers se publican por año en machine learning e IA en arXiv. En 2012 había menos de 3.000 por año. En 2017, con los Transformers, saltó a 10.000. Con GPT-3 en 2020 superó los 40.000. En 2025 llegó a casi 115.000. La barra de 2026 es parcial y ya va camino a superar a 2025.

No se puede leer todo. Elegí los más relevantes para Context Rot.

---

## SLIDE 4 — Cómo funciona un LLM (45s)

Para entender por qué existe Context Rot, necesito explicar cómo funciona un LLM sin matemática. Un LLM predice palabras: dado todo lo anterior, predice cuál sigue. Antes de elegir cada palabra, decide a qué parte del contexto prestarle atención. Eso se llama mecanismo de atención.

La atención es un recurso finito que se reparte entre todos los tokens del contexto. Mientras la conversación es corta, le sobra. A medida que crece, cada token recibe menos.

Y miren la tabla: la ventana de contexto pasó de 16 mil tokens en 2023 a un millón en 2026 — el equivalente a dos mil páginas. Las instrucciones del principio compiten por atención con todo lo que se acumula después.

---

## SLIDE 5 — Trayectoria de la literatura (30s)

Treinta años de historia, de Bengio en el 94 hasta los Transformers en 2017. Recién en 2024-25 el campo empieza a estudiar el problema en conversaciones largas.

En los próximos tres slides desarrollo esto. Quiero mostrar que el problema viene de cómo está construida la arquitectura.

---

## SLIDE 6 — La era pre-Transformers (50s)

Yoshua Bengio es uno de los padres del deep learning moderno, Premio Turing 2018. En 1994, con Simard y Frasconi, demostró matemáticamente que las redes neuronales recurrentes no pueden aprender dependencias a largo plazo. Los gradientes se desvanecen. El olvido en redes queda formalmente demostrado.

Bengio hoy lidera el debate en AI Safety. Firmó la carta de pausa de 2023, preside el International AI Safety Report encomendado por 30 países y este año fundó LawZero. El problema que describió en el 94 sigue conectado con la seguridad de los sistemas de hoy.

Tres años después, Hochreiter y Schmidhuber proponen las LSTMs: redes con compuertas que regulan qué guardar y qué olvidar. Dominaron NLP durante 20 años. Pero la arquitectura es secuencial y difícil de escalar.

---

## SLIDE 7 — La era Transformers (50s)

En 2017, Vaswani y colegas en Google publican "Attention Is All You Need". Se deshacen de la recurrencia y la reemplazan por atención pura. Los Transformers son la base de todos los LLMs modernos: GPT, Claude, Gemini, Llama.

Tres años después, Brown y colegas en OpenAI publican "Language Models are Few-Shot Learners", el paper de GPT-3. 175 mil millones de parámetros. Lo que demuestran es que al escalar los Transformers aparecen capacidades emergentes como in-context learning y la capacidad de seguir instrucciones.

Y en 2022, Ouyang y colegas publican el paper de InstructGPT: "Training Language Models to Follow Instructions with Human Feedback". Ahí está la técnica de RLHF que hizo posible ChatGPT. Cuando OpenAI lanza el modelo al público en noviembre, ChatGPT gana 100 millones de usuarios en dos meses. Los LLMs salen del laboratorio.

---

## SLIDE 8 — Por qué los Transformers no resolvieron el olvido (35s)

Acá el punto central. Las LSTMs tenían memoria explícita por diseño, pero no escalaban. Los Transformers resuelven la escala, pero a cambio no tienen memoria explícita. Solo atención global, y la atención es finita.

Los Transformers escalaron sacrificando memoria explícita. Cuando el contexto crece, la atención global se diluye. Eso es Context Rot.

---

## SLIDE 9 — Laban et al. 2025 (60s)

El primer paper central es Laban y colegas, preprint de Microsoft Research y Salesforce. Compararon el mismo modelo en dos settings: single-turn fully-specified, donde dan toda la información de una sola vez, y multi-turn sharded, donde la fragmentan en turnos. 15 modelos, 6 tareas de generación.

Resultado: caída del 39% entre single-turn y multi-turn. En los 15 modelos, sin excepciones.

Un dato que nos importa: la capacidad del modelo solo baja 16%. La varianza sube 112%. La aptitud cae poco; lo que explota es la inestabilidad. Eso conecta con el marco bayesiano que retomo al final del talk.

Y acá está **la brecha que justifica todo este trabajo**: ninguno de los papers, incluido Laban, desagrega los resultados por tipo de instrucción. Tratan a todas las instrucciones por igual. Ese es exactamente el hueco que el proyecto final va a llenar.

---

## SLIDE 10 — He et al. 2024, Meta (50s)

El segundo paper de medición es Multi-IF, de He y colegas en Meta. En cada turno se agrega una instrucción nueva al contexto, sin sacar las anteriores. Definen una métrica clara: Instruction Forgetting Ratio, el porcentaje de instrucciones que el modelo cumplió antes pero deja de cumplir después.

14 modelos, 8 idiomas, 4.501 conversaciones. Resultado: o1-preview cae de 87,7 a 70,7 por ciento en solo 3 turnos.

Las instrucciones están en el contexto pero el modelo deja de usarlas. Y los autores reconocen que las conversaciones reales tienen 10 o más turnos, así que el problema real es probablemente peor.

---

## SLIDE 11 — Liu et al. 2024 (60s)

Liu y colegas, en un paper publicado en TACL 2024, se enfocaron en el mecanismo. Testearon dos tareas: QA sobre múltiples documentos, y recuperación clave-valor sintética. Variaron la posición del item relevante en el contexto. Siete modelos.

Resultado: curva U asimétrica. El inicio se retiene mejor que el final; el medio se pierde más que ambos. GPT-3.5 cae de 75% al inicio a 52% en el medio.

Algo importante sobre lo que el paper dice y lo que estoy extrapolando: el paper documenta el efecto pero no mide atención directamente. La conexión entre la posición cero y el system prompt es mi extrapolación, no algo que ellos digan.

Limitación de los autores: tareas de recuperación en inglés; ni instrucciones ni casos realistas.

---

## SLIDE 12 — Mu et al. 2025 (45s)

El segundo mecanismo es de Norman Mu y colegas, en UC Berkeley. El paper se llama "A Closer Look at System Prompt Robustness". Diseñaron el Monkey Island stress test: agregaron entre 1 y 20 guardrails a un system prompt real, manteniendo modelo y tarea fijos. Cinco modelos.

Resultado: al pasar de 1 a 20 reglas, la adherencia a cada una se aproxima a cero, en todos los modelos.

Un dato fuerte: en system prompts reales del GPT Store de OpenAI, el promedio es 5.1 guardrails. La producción ya opera cerca de la zona problemática.

Mecanismo distinto al de Liu: ahí el problema es la posición. Acá es la cantidad.

---

## SLIDE 13 — Implicaciones de seguridad (60s)

Hasta acá vimos Context Rot como problema de performance. Dos trabajos lo enmarcan como problema de seguridad.

Anil y colegas en Anthropic, en 2024, midieron empíricamente que la tasa de jailbreak —cuando un usuario consigue que el modelo haga algo prohibido— aumenta sistemáticamente con el número de ejemplos previos en el contexto. Más largo significa más vulnerable. Lo llamaron "many-shot jailbreaking".

Rivasseau, en 2025, hace la formalización teórica: el ratio de tokens del system prompt sobre el contexto total tiende a cero a medida que la conversación crece. Propone interrupciones periódicas, sin evaluación empírica todavía.

La implicación es directa: los guardrails son instrucciones como cualquier otra. Si los guardrails decaen, no salta nada: el sistema falla y no te enterás.

---

## SLIDE 14 — Repetir el prompt (30s)

Ahora, qué se hace para mitigarlo. La primera "solución", sin paper formal: repetir el system prompt completo al principio de cada turno. Es lo que hace la mayoría de los sistemas en producción.

Lo sabido: el costo es N veces los tokens del system prompt. Mu mostró que más reglas pueden empeorar la situación. Pero nadie midió sistemáticamente esta práctica en conversaciones largas reales.

---

## SLIDE 15 — Wallace et al. 2024, OpenAI (40s)

Wallace y colegas en OpenAI propusieron una jerarquía de instrucciones. Entrenaron GPT-3.5 Turbo para priorizar por origen: primero system, después usuario, después contenido multimodal, después salidas de herramientas. La jerarquía se aprende en el entrenamiento, no se impone en contexto.

Mejoras: +63% en robustez frente a extracción del system prompt, +30% frente a jailbreaks. Limitación reconocida: over-refusal.

Mi extensión: la jerarquía ordena roles, no instrucciones individuales. Dentro de un mismo rol, no aborda el decay temporal.

---

## SLIDE 16 — Leviathan et al. 2025, Google Research (35s)

Leviathan y colegas en Google publicaron a fines de 2025 un enfoque distinto. Duplican el prompt entero, uno detrás del otro: toman la query y la repiten inmediatamente después.

La intuición: la atención causal impide que los tokens iniciales atiendan a los posteriores. Repetir permite una segunda pasada. Resultado: 47 victorias y 0 derrotas sobre 70 combinaciones, en modelos sin chain-of-thought.

Limitación: duplica los tokens de entrada. Y sigue siendo uniforme: duplica todo el prompt por igual, sin priorizar.

---

## SLIDE 17 — Dongre et al. 2025 (35s)

Dongre y colegas en Adobe Research y UIUC, preprint de arXiv. En conversaciones de 10 turnos del benchmark τ-Bench, inyectaron recordatorios del objetivo en turnos fijos t=4 y t=7. Tres modelos como simuladores de usuario.

Hallazgo central: el drift se estabiliza en un equilibrio finito; no crece sin techo. Los recordatorios bajan ese equilibrio.

Limitación: el calendario es fijo, no adaptativo. No deciden qué instrucción reinyectar según su historial.

---

## SLIDE 18 — Comparación de mitigaciones (30s)

Acá el resumen comparativo. Cuatro estrategias, cuatro costos, cuatro límites distintos.

Lo que tienen en común es que todas son uniformes: tratan al conjunto de instrucciones como un solo bloque.

---

## SLIDE 19 — Marco teórico y lo que falta (65s)

Dos trabajos dan el marco teórico para una solución más sofisticada.

Zhang, Yang y Wang en 2025 mostraron que los LLM se comportan como filtros bayesianos descontados, con un factor gamma menor a uno: el prior pierde peso frente a las observaciones recientes. Probaron esto en modelos chicos con tareas de actualización de creencias, no en instrucciones. El puente con olvido de compliance lo hago yo. **Y conecta directamente con el hallazgo de Laban: la varianza del 112% es exactamente lo que un posterior bayesiano inestable produce.**

Greenblatt y colegas en ICML 2024, desde Redwood Research, definieron AI Control: garantizar seguridad en runtime asumiendo que el modelo puede subvertir sus salvaguardas. Proponen protocolos externos. Lo menciono como marco complementario; las salvaguardas que ellos diseñan quedan expuestas si cualquier instrucción del system prompt decae.

Con esos dos marcos, lo que falta queda claro. Ya lo dijimos en Laban: nadie midió si el decay varía según el tipo de instrucción. Sin esa medición, cualquier sistema de refuerzo selectivo es injustificado. Anthropic, OpenAI, Google y Meta no publicaron investigación primaria sobre Context Rot. Las mitigaciones son uniformes porque no tienen datos para discriminar entre instrucciones.

---

## SLIDE 20 — Orientación del proyecto final (50s)

Ante esa brecha, antes de proponer un sistema selectivo había que verificar el supuesto: ¿realmente las instrucciones decaen distinto?

Hice un estudio para responderlo. 28 conversaciones, 244 observaciones, 5 modelos, modelo logístico ordinal bayesiano con efectos jerárquicos por tipo de decisión.

Resultado: sigma beta igual a 2,11, intervalo de credibilidad del 94% entre 1,06 y 3,28. La heterogeneidad existe.

El siguiente paso es armar un sistema Bayesian Knowledge Tracing con presupuesto fijo de tokens y compararlo contra el refuerzo uniforme que vimos.

El trabajo está sometido a JAIIO 55; los resultados se anuncian a fines de mayo. No es resultado validado por pares todavía. Gracias.

---

## SLIDE 21 — Referencias (8s)

*(Mostrar y decir:)* Las referencias están acá. Si les interesa profundizar en algún paper, lo charlamos después.

---

# Notas para el expositor

## Tiempos estimados (más realistas)

| # | Slide | Tiempo |
|---|-------|--------|
| 1 | Título | 12s |
| 2 | Delimitación | 25s |
| 3 | Explosión arXiv | 35s |
| 4 | Cómo funciona LLM | 45s |
| 5 | Trayectoria | 30s |
| 6 | Era pre-Transformers | 50s |
| 7 | Era Transformers | 45s |
| 8 | Por qué no resolvieron | 35s |
| 9 | Laban 2025 | 60s |
| 10 | He 2024 | 50s |
| 11 | Liu 2024 | 60s |
| 12 | Mu 2025 | 45s |
| 13 | Implicaciones seguridad | 60s |
| 14 | Repetir prompt | 30s |
| 15 | Wallace 2024 | 40s |
| 16 | Leviathan 2025 | 35s |
| 17 | Dongre 2025 | 35s |
| 18 | Comparación | 30s |
| 19 | Marco + lo que falta | 65s |
| 20 | Orientación + JAIIO | 50s |
| 21 | Referencias | 8s |

**Total: ~13:30.** Te queda margen de 90 segundos. Si hablás más lento, llegás a 15:00 cómodo.

## Recortes adicionales si todavía te pasás

Por orden de prioridad para cortar:

1. **Slide 8** (por qué no resolvieron): si te apurás, podés decir solo la última frase y saltar. Ahorro: 25s.
2. **Slide 3** (explosión arXiv): podés saltar el conteo año por año y solo decir "de 3.000 a 115.000 papers por año entre 2012 y 2025". Ahorro: 15s.
3. **Slide 11** (Liu): la parte de "honestidad sobre lo que extrapolamos" se puede comprimir. Ahorro: 15s.
4. **Slides 16 y 17** (Leviathan y Dongre): saltar la "intuición" o el "hallazgo central" si vas tarde. Ahorro: 15s cada uno.

## Si quedás corto

- **Slide 11 (Liu)**: la honestidad sobre lo que el paper mide vs lo que extrapolamos es un punto fuerte para desarrollar.
- **Slide 13 (seguridad)**: conectar más con AI Safety actual, mencionando a Bengio nuevamente o las preocupaciones recientes.

## Tips de pacing

- **Pausas:** dejá pausas reales entre slides (1-2 segundos). Eso hace que la audiencia procese y vos respirás.
- **Números:** cuando digas "87.7 → 70.7%", hacelo lento. Es info densa.
- **Transiciones:** entre slides, podés decir frases cortas tipo "ahora viene el mecanismo" o "pasamos a las mitigaciones". Te dan oxígeno sin agregar contenido.

## Cosas a saber bien (para preguntas)

- **METR / reward hacking:** no lo incluí porque METR dice que reward hacking no es Context Rot — los modelos entienden y eligen no cumplir. Modo de falla paralelo, no la misma causa.
- **Si te preguntan por el paper de JAIIO:** "Está sometido a JAIIO 55, se anuncia a fines de mayo. Lo menciono porque establece el prerrequisito empírico del proyecto final, pero no es resultado validado todavía."
- **Si te preguntan por un paper que no incluiste:** "El campo genera más de 100.000 papers por año. Esta es una revisión de los más relevantes para el problema específico de Context Rot."
- **Algo que no sabés:** "Buena pregunta, eso entra en el proyecto final — todavía no llegué a esa parte."

## Contexto por paper (para defenderte)

- **Laban 2025:** 39% es promedio sobre 15 modelos × 6 tareas, comparando single-turn vs multi-turn. Aptitud baja 16%, varianza sube 112%.
- **He 2024:** instrucciones acumuladas turno a turno, no todas al principio. 87.7→70.7 es o1-preview específicamente.
- **Liu 2024:** dos tareas, no solo doc QA. Paper no mide atención, eso es interpretación mía.
- **Mu 2025:** 1-20 guardrails, no 50. Promedio real en GPT Store: 5.1.
- **Anil et al. 2024 (Anthropic):** evidencia empírica del jailbreak-vs-length (many-shot jailbreaking). NeurIPS.
- **Rivasseau 2025:** contribución teórica, no empírica.
- **Wallace 2024:** 4 niveles, solo GPT-3.5 Turbo.
- **Leviathan 2025:** duplicación back-to-back, 7 modelos, 7 benchmarks. Solo input tokens duplican; latencia generalmente igual.
- **Dongre 2025:** un solo paper. 10 turnos (τ-Bench), reminders en t=4 y t=7. Adobe + UIUC. Preprint arXiv (no AAAI confirmado).
- **Zhang, Yang & Wang 2025:** 3 autores. Modelos chicos, tareas de belief updating (no instrucciones).
- **Greenblatt 2024:** Redwood Research. Protocolos externos, no instrucciones en contexto.
- **Tu estudio:** σ_β = 2.11. 3 tipos benefician del refuerzo, 1 empeora (negación), 8 no cambian.
