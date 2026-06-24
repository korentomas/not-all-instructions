Estás usando ChatGPT. Le explicás tu proyecto, le pedís que siga ciertas reglas, y funciona bárbaro. Van y vienen mensajes. Todo bien.

Hasta que en el mensaje 15... te responde cualquier cosa. Como si nunca le hubieras dicho nada.

¿Qué pasó?

---

Para entender por qué pasa esto, necesitamos entender un poco cómo funciona un LLM por dentro. Un Large Language Model no "entiende" nada. Es una máquina de predicción de texto: dado todo lo anterior, predice qué palabra viene después. Pero esa predicción es mucho más sofisticada de lo que parece.

El año pasado, Anthropic — la empresa detrás de Claude — le hizo reverse engineering a uno de sus modelos y publicó lo que encontró adentro. Y es fascinante. Primero: no procesa paso a paso como haríamos nosotros. Evalúa múltiples caminos en paralelo y "vota" entre ellos. Segundo: planifica hacia adelante. Puede elegir una palabra que va a decir al final de una oración antes de escribir el principio de esa oración. ¿Cómo lo hace? Con circuitos internos.

---

Esta imagen viene del paper de Anthropic. Es un ejemplo real de cómo razona el modelo. Le preguntás: "¿Cuál es la capital del estado donde está Dallas?" Y el modelo no busca la respuesta directamente. Encadena representaciones internas: activa "Dallas", eso activa "Texas", eso se combina con "capital", y llega a "Austin". Cada uno de estos nodos es lo que en interpretabilidad llaman un feature — una representación interna, no confundir con feature de un dataset. Son conceptos que el modelo aprendió y que se activan según el contexto.

---

Ahora, para generar cada palabra, el modelo tiene que decidir a qué parte de todo el texto prestarle atención. Esto se llama, literalmente, el mecanismo de atención. Cuando el contexto es corto — unos pocos miles de tokens — esto funciona bien. Hay pocos tokens y el modelo puede atender a cada uno. Pero la atención es un recurso finito. Se reparte entre todos los tokens del contexto. Y cuando el contexto crece, las instrucciones que le diste al principio tienen que competir con todo lo que vino después. Entonces la pregunta es: ¿qué pasa cuando hay un millón de tokens compitiendo por atención?

---

Primero, definiciones rápidas. Un token es la unidad mínima que procesa el modelo. Una palabra es más o menos uno o dos tokens. Una página son unos 500 tokens. La ventana de contexto es todo lo que el modelo puede "ver" al generar una respuesta: el system prompt, toda la conversación, los archivos adjuntos. Si algo no está en la ventana, el modelo no lo sabe. No tiene memoria aparte. Y mirá cómo creció esto: en 2023, la ventana más grande era de 16 mil tokens. Hoy estamos en un millón. Eso es el equivalente a dos mil páginas. Un libro entero cabe en una sola conversación. Más ventana debería ser mejor, ¿no?

---

Antes de hablar del problema, necesitamos hablar de las instrucciones. El system prompt son las instrucciones que recibe el modelo antes de hablar con el usuario. Cosas como: "respondé en español", "sos un tutor amable", "no generes contenido dañino", "usá tal herramienta para tal tarea". A las instrucciones de seguridad les decimos guardrails. Y acá hay algo importante: los guardrails no son un módulo especial. El modelo no tiene un botón de "seguridad". Son instrucciones como cualquier otra. Acá a la derecha ven el circuito real de rechazo de Claude, del paper de Anthropic. Es un pathway — un camino de activaciones. No es un interruptor. La seguridad depende de que el modelo siga atendiendo a esas instrucciones.

---

Acá es donde la cosa se pone interesante. Hay una serie de papers de los últimos dos años que miden esto. Laban y colegas en 2025 midieron una caída del 39% en tareas conversacionales de varios turnos. El equipo de Meta con el benchmark Multi-IF mostró que la precisión baja de 87.7% a 70.7% en solo 3 turnos. Chroma Research testeó 18 modelos frontera — y los 18 muestran el mismo patrón. Y Mu y colegas mostraron que cuando le ponés más de 50 reglas al system prompt, la adherencia se acerca a cero. No es un bug de un modelo. Le pasa a todos.

---

¿Y por qué pasa? En parte lo explica este fenómeno que descubrió Liu y colegas en 2023, conocido como "Lost in the Middle." Cuando medís la precisión del modelo según dónde está la información en el contexto, aparece esta curva U. Lo que está al principio lo atiende bien. Lo que está al final, también. Pero lo que queda en el medio se pierde. Esto se midió originalmente en tareas de recuperación de información, no directamente en instrucciones. Pero el patrón sugiere que la atención no es uniforme — y eso podría explicar por qué las instrucciones también se degradan a medida que el contexto crece.

---

¿Y por qué nos debería importar? Hay dos ángulos. Primero, plata. Las empresas que operan estos modelos procesan miles de millones de tokens por día. Cada token de reminder extra tiene un costo. Si el refuerzo es ineficiente — si estás repitiendo todo a lo bruto — el costo se multiplica a escala. Segundo, seguridad. Los guardrails de seguridad son instrucciones como cualquier otra. Nuestra hipótesis es que podrían decaer más rápido que las instrucciones de formato. Y si es así, los reminders uniformes están sub-invirtiendo en seguridad. Para ponerlo concreto: le pedís al modelo que solo cite fuentes reales. 10 turnos después, te inventa un paper que no existe.

---

¿Y qué se hace hoy para resolver esto? Básicamente, cuatro estrategias. Repetir todo el prompt cada turno — pero eso satura: más reglas terminan produciendo menos adherencia, no más. Duplicar el prompt — poner las instrucciones dos veces. Google publicó un paper sobre esto en 2025. Funciona, pero duplica el costo en tokens. No hacer nada — confiar en que el modelo recuerda. Ya vimos: 39% de caída. Y la jerarquía de instrucciones de OpenAI, donde el system prompt tiene prioridad sobre el usuario. Eso es estático — no aborda el decaimiento gradual. El punto es: ninguna de estas estrategias es adaptativa. Ninguna decide qué reforzar ni cuándo.

---

Si sabemos que el modelo olvida... y sospechamos que cada instrucción decae distinto... ¿por qué reforzamos todo por igual? ¿Y si pudiéramos reforzar solo lo que se está por olvidar?

---

Acá es donde entra lo bayesiano. El enfoque clásico es binario. ¿Cumple la instrucción? Sí o no. Si cumple, no hacemos nada. Si no cumple, ya es tarde. Y no distingue entre una instrucción que está al 90% de probabilidad de ser cumplida y una que está al 51%. El enfoque bayesiano es distinto. Mantenemos un posterior para cada instrucción. Cada vez que observamos si el modelo cumplió o no, actualizamos la estimación — verosimilitud por prior. Y entre turnos, ese posterior decae naturalmente. Esto nos deja anticipar el olvido antes de que pase, en vez de reaccionar cuando ya es tarde.

---

Esto no es una idea nueva. BKT — Bayesian Knowledge Tracing — se usa hace 30 años en educación. Estima la probabilidad de que un estudiante domine un concepto, turno a turno. Observás si respondió bien, actualizás tu creencia, y entre sesiones esa creencia decae porque el estudiante puede olvidar. Acá ven el ciclo: observación, actualización bayesiana, creencia actualizada, y decaimiento entre turnos. La inversión conceptual es esta: ¿qué pasa si el "estudiante" es el LLM y los "conceptos" son sus instrucciones?

---

Y la formalización es directa. Para cada instrucción i en el turno t, la probabilidad de que siga siendo cumplida es un Bayes update clásico. La verosimilitud de lo que observamos, por lo que creíamos antes — nuestro prior — sobre la evidencia total. Gamma menor a 1 controla cuánto decae entre turnos. Y la idea clave es: si tenés un presupuesto fijo de B tokens para reminders, reforzás solo las instrucciones con menor probabilidad de compliance. Nadie aplicó BKT a compliance de LLMs, ni midió curvas de olvido por tipo de instrucción, ni optimizó qué reforzar con un presupuesto limitado de tokens. Eso es lo que propongo investigar.

---

Eso es todo. ¿Preguntas?
