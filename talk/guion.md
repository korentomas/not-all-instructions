# Guión — Not All Instructions Are Forgotten Equal

55 JAIIO, ASAID 2026. Slot de 20 minutos, 17 sugeridos de exposición.
Objetivo hablado: 13:00, para que el margen absorba preguntas y cambio de orador.

Deck de referencia: `Korenblit_Tomas_Not_All_Instructions-3.pdf`, 24 slides
principales + backup (25–32).

---

## 1. Título (30s)

Hola, soy Tomás Korenblit, estudiante de grado de Ciencia de Datos en la
Universidad Nacional de San Martín.

Les voy a hablar de un trabajo sobre adherencia a instrucciones en modelos de
lenguaje. El título es "no todas las instrucciones se olvidan igual", y en los
próximos minutos van a ver por qué.

*(Si el meme se rió solo, no lo expliques. Seguí.)*

---

## 2. Robot bebé (40s)

Cuando arrancás una conversación con un agente, el modelo está fresco, la
ventana vacía, y le tirás todo junto. Una docena de instrucciones de todo tipo.

Algunas triviales: no uses emojis. Algunas operativas: no pushees a main, no
corras código. Algunas que si fallan te arruinan el día: no borres la base de
datos.

*(pausa breve, señalás el globo rojo)*

Y algunas donde ya no estamos hablando de estilo de código.

En los primeros turnos las cumple casi todas.

---

## 3. Chevrons (10s)

Adelantemos veinte turnos.

*(Pausa real. Dejá que la pantalla oscura haga el trabajo. Contá hasta dos.)*

---

## 4. Robot anciano (50s)

Cien mil tokens de archivos, herramientas y razonamiento después.

Las instrucciones del principio ahora compiten por atención contra todo lo que
vino después: lo que le fuiste pidiendo en el medio, el reasoning del modelo,
los documentos que abrió, las herramientas que llamó.

Y algo se pierde. Miren qué quedó nítido.

*(pausa)*

"No uses emojis". Y miren cuál está tachada.

Aclaro algo antes de seguir, porque si no me lo van a preguntar con razón:
**ninguna de estas seis la medí yo.** Esto es la intuición. En un minuto les
muestro qué pasa cuando uno lo mide de verdad.

---

## 5. Agenda (20s)

El plan es este. Primero el problema, que es dónde estamos parados hoy. Después
cómo lo medí. Después qué encontré. Y al final por qué esto importa más allá
del estilo de código.

---

## 6. Atención posicional — Liu (35s)

Esto no lo descubrí yo, está bien documentado y se sabe por qué pasa.

Liu y colegas midieron precisión según dónde está la información relevante
dentro del contexto. Y aparece esta curva en U: lo que está al principio pesa,
lo que está al final pesa, y lo que queda en el medio se pierde.

Por eso una instrucción en el system prompt, que ocupa la posición cero,
aguanta mejor que una preferencia que dijiste a mitad de conversación.

Una honestidad: el paper mide recuperación de información, no instrucciones.
Esa extrapolación la hago yo.

---

## 7. Saturación de guardrails — Mu (35s)

El segundo mecanismo es distinto. Acá el problema no es la posición, es la
cantidad.

Mu y colegas fueron agregando guardrails a un system prompt real, de uno a
veinte, con el modelo y la tarea fijos. Y la adherencia a cada regla
individual se va a cero. En los cinco modelos, razonadores incluidos.

El dato que más me gusta de ese paper: en system prompts reales del GPT Store
el promedio es cinco reglas. O sea que producción ya está operando adentro de
esta curva.

---

## 8. La pregunta, primer paso (25s)

*(En pantalla las tres líneas; la resaltada es la de abajo.)*

Si el modelo olvida, y eso ya lo vimos medido… ¿olvida todo por igual?

No lo sabemos. Pero miren lo que sí hacemos: las mitigaciones que existen
refuerzan todo por igual. Recordatorios periódicos, repetir el prompt, todas
tratan a las doce instrucciones como si fueran la misma.

Entonces: **¿por qué reforzamos todo por igual?**

---

## 9. La pregunta, segundo paso (15s)

*(click, el resaltado sube a la línea del medio)*

Porque esta pregunta nadie la midió. Los estudios que les mostré reportan un
promedio sobre el conjunto de instrucciones.

*(pausa)*

¿Olvida todo por igual? Eso es lo que vine a medir.

---

## 10. Ejemplo de una conversación (60s)

Así se ve un experimento.

Turno 1: planto la instrucción como lo que es en la vida real, un pedido al
pasar del usuario. "Usá numpy broadcasting, nada de for loops."

Después la conversación sigue. Entran archivos del repositorio, tareas,
herramientas. El contexto crece.

Turno 20: le pido algo normal. Escribir una función que normalice un array.

Y acá está la parte importante del diseño: **ese pedido no menciona
broadcasting.** No le recuerdo nada. Solo le doy la oportunidad de cumplir, o
de no cumplir.

Lo que salga se puntúa con una regla fija.

---

## 11. El diseño (60s)

Doce instrucciones por conversación, la mitad plantadas temprano y la mitad
tarde, para que no queden todas igual de enterradas.

Seis turnos de prueba al final, cada uno prueba dos instrucciones.

Tres repositorios open source de verdad: Bambi, ArviZ y PyMC. Y no son tres
cualesquiera, son tres niveles de presión de contexto, de 98 mil a 203 mil
tokens.

Cinco modelos, de 26 a 120 mil millones de parámetros. Aclaro desde ya que el
control lo corrí solo con Qwen, y vuelvo a eso en limitaciones.

Y lo último es lo que hace falsable todo lo demás: corrí **las mismas
conversaciones sin introducir ninguna instrucción**. Sin ese control no sabría
si el modelo cumple porque se lo pedí o porque lo iba a hacer igual.

---

## 12. Cómo se puntúa (45s)

Cada respuesta la puntúa una regla fija, no un juez. Para parametrize, busca el
decorador en el código.

La escala va de 0 a 3. Tres es cumple. Cero es falla **teniendo la
oportunidad**.

Y esa distinción importa: si el modelo no escribió ningún test, ese turno no se
puntúa, se excluye. Si no, estaría contando como violación un caso donde la
oportunidad nunca existió.

¿Por qué así y no con un modelo juzgando? Porque es determinista y
reproducible, y no depende de que otro modelo tenga un buen día.

---

## 13. El modelo, escala latente (50s)

El puntaje es ordinal: cero, uno, dos, tres están ordenados, pero la distancia
entre ellos no es comparable. Así que no puedo promediarlos como números.

El modelo dice: detrás de cada respuesta hay una cantidad continua que no
vemos, el cumplimiento latente. Lo que sí vemos es en qué cajón cayó. Tres
cortes parten la recta en cuatro tramos.

Elegí cuatro instrucciones que cuentan toda la historia. Testing parametrize:
sin instrucción vive en la zona del cero, con instrucción salta hasta el tres.
Module constants: un salto más chico. Docs numpy style: ya estaba arriba de
todo, decirlo casi no la mueve, eso es techo. Y dependencies no new
**retrocede**: el punto lleno queda a la izquierda del vacío. Guarden esa,
vuelvo sobre ella.

---

## 14. El modelo, la ecuación (30s)

Formalmente es un modelo de odds proporcionales. Ésta es la forma en que lo
escribe McElreath; abajo está como lo escribí yo, la misma ecuación por el
complemento.

Fíjense en algo: **el beta es uno solo para los tres umbrales**, no uno por
umbral. Ese supuesto se llama odds proporcionales y es exactamente lo que me
deja hablar de un efecto por instrucción en vez de tres.

Los alfas y betas de las doce instrucciones comparten distribución, partial
pooling, con priors centrados en cero. Las cuatro líneas del modelo están en
backup si alguien las quiere ver.

---

## 15. Datos (35s)

Antes del modelo, los datos crudos. Gris es sin instrucción, azul es con
instrucción.

Miren la forma general: en buena parte de las instrucciones las dos barras
están casi a la misma altura y bastante arriba. El modelo ya lo hacía solo.

Y miren la izquierda, donde el gris directamente no llega. Ahí decirlo cambia
todo.

Ya se ve a ojo que esto no es parejo. El modelo lo que hace es ponerle
incertidumbre a esa impresión.

---

## 16. Forest, primer paso (30s)

Acá está el efecto de decir cada instrucción, con su intervalo de credibilidad
del 94%.

Tres instrucciones tienen el intervalo entero por encima de cero. Testing
parametrize es la más extrema: el modelo prácticamente nunca usa
`pytest.mark.parametrize` si no se lo pedís, y cuando se lo pedís lo usa.

---

## 17. Forest, segundo paso (30s)

*(click)*

Y estas ocho son no concluyentes. Ojo con cómo se lee esto, porque es la parte
que más se malinterpreta: no concluyente **no** significa que la instrucción se
perdió. En la mayoría de estos casos el modelo ya cumplía por defecto, así que
decirlo no cambia gran cosa.

Desde afuera, con una métrica promedio, "ya lo hacía" y "se perdió" se ven
exactamente igual. Por eso hace falta el control.

---

## 18. Forest, completo (35s)

*(click)*

Y una da negativo, la que les pedí que guardaran.

Antes de que saquen conclusiones sobre esa: no crean que decir una instrucción
empeora el cumplimiento. Vuelvo a eso en limitaciones.

Lo que quiero que se lleven de esta figura es la dispersión. Los efectos van de
menos 2,4 a más 5,4 en log-odds. Eso es sigma beta igual a 2,1, con el
intervalo lejos del cero, y es el resultado central del trabajo.

Y una aclaración que me van a agradecer: **esto no es capacidad con otro
nombre.** La retención no sube del modelo de 26 mil millones al de 120 mil
millones. Si esto fuera una cuestión de qué tan bueno es el modelo, el más
grande cumpliría más, y no pasa.

---

## 19. Qué conviene reforzar (45s)

Ahora, esto es lo accionable. Traduje el efecto a probabilidad: cuánto sube la
chance de que el modelo cumpla si repetís la instrucción.

Abajo, en azul, tres instrucciones donde repetir paga. En el medio, un montón
donde la ganancia es prácticamente cero, porque ya se cumplían solas.
Repetirlas es gastar tokens para no mover nada.

Una política uniforme, que es lo que se hace hoy, paga por las doce. Con esto
podés pagar por tres.

Una advertencia importante: **una ganancia baja no es motivo para descartar una
regla de seguridad.** Esto te dice dónde ahorrar repetición en preferencias
ordinarias, no qué salvaguardas podés dejar de decir.

---

## 20. Limitaciones (50s)

Cuatro cosas.

Primero, ese efecto negativo: ¿finding o artefacto? Mi sospecha es artefacto de
la regla: contaba como import nuevo cualquiera, incluidos los que ya estaban en
el archivo y el modelo vuelve a mostrar al reescribirlo. Ya la corregí en el
repositorio, pero los números que les muestro son los del paper, con la regla
vieja.

Segundo, esto es una foto en los turnos 20 a 25, no una curva. No puedo decir a
qué turno empieza a caer ni estimar una tasa de olvido.

Tercero, y es el más importante: **planté preferencias de código, no
salvaguardas.** Y quiero ser explícito en qué dirección puede fallar esto: es
probable que mi proxy **exagere** la fragilidad, porque una salvaguarda real
vive en el system prompt, que es la posición más estable, y encima se refuerza
en entrenamiento. Mi resultado aplica más directo a restricciones dichas en
contexto.

Cuarto, el control viene de un solo modelo. Hice el chequeo que se puede hacer:
reajusté todo solo con datos de Qwen, y los efectos correlacionan a 0,80 con
los del modelo completo. Mitiga, no elimina.

---

## 21. Por qué es importante, safety (45s)

Dicho eso, por qué creo que igual importa.

Una preferencia de código y una salvaguarda son el mismo tipo de objeto: una
instrucción dicha una vez que después compite por atención contra todo lo que
se acumula.

¿El contexto sabe que una importa más que la otra? No. Se degradan por la misma
física.

Y hay algo que hace esto peor de lo que parece. La seguridad es conjuntiva:
alcanza con que falle una. Así que el cumplimiento promedio puede verse
perfectamente sano mientras la única regla que importaba ya se cayó. Un agente
desplegado no tiene un usuario que note y repita. Falla en silencio.

Por eso creo que esto se mide por instrucción o no se mide.

---

## 22. Conclusiones (40s)

Tres cosas.

La heterogeneidad entre instrucciones es grande. No es un detalle de segundo
orden, es el efecto principal.

Solo tres de doce pagan el refuerzo, mientras que una política uniforme gasta
en las doce.

Y medir por instrucción es lo que habilita monitoreo selectivo. La dirección
natural es Bayesian Knowledge Tracing, que es un marco que en educación estima
qué concepto domina un estudiante turno a turno. Acá el estudiante es el modelo
y los conceptos son sus instrucciones. Eso todavía no está construido: este
trabajo mide el supuesto que lo haría útil.

---

## 23. Gracias (10s)

Gracias. El agradecimiento a BlueDot Impact por el Rapid Grant está en
pantalla, y lo digo también: sin ese apoyo esto no hubiera sido posible.

Quedo para preguntas.

---

## 24. Referencias (5s)

*(No la leas. Dejala en pantalla mientras arrancan las preguntas, o pasala
directo a la de gracias si el moderador ya está hablando.)*

Las referencias quedan acá, y están también en el repositorio.

---

# Notas para el expositor

## Tiempos

| Bloque | Slides | Tiempo |
|---|---|---|
| Apertura | 1–4 | 2:10 |
| Contexto | 5–9 | 2:10 |
| Metodología | 10–12 | 2:45 |
| Modelo | 13–14 | 1:20 |
| Resultados | 15–19 | 2:55 |
| Cierre | 20–24 | 2:30 |
| **Total** | | **≈ 13:00** |

Con slot de 20 y 17 sugeridos, 13:00 hablado deja margen real.

## Si vas largo, cortá en este orden

1. **Slide 14** (la ecuación de McElreath). La frase de odds proporcionales ya
   está anotada en la slide; decila en una línea y pasá. Ahorro: 30s.
2. **Slide 7** (Mu). Con Liu alcanza para instalar el mecanismo. Ahorro: 35s.
3. **Slide 15** (datos crudos). Vas directo al forest. Ahorro: 35s.

## Si vas corto

- Slide 19, desarrollá el ejemplo concreto: le pedís que solo cite fuentes
  reales, diez turnos después te inventa un paper que no existe.
- Slide 21, contá el incidente de Replit: borró una base de producción durante
  un code freeze explícito, y después reportó mal lo que había hecho.

## Pausas que no se negocian

- Después de "adelantemos veinte turnos" (slide 3). Dos segundos reales.
- Después de "miren qué quedó nítido" (slide 4), antes de decir "no uses
  emojis".
- Después de "¿por qué reforzamos todo por igual?" (slide 8), antes del click
  a la 9.

## Mapa de backup (slides 25–32)

| Slide | Contenido | La usás si preguntan por… |
|---|---|---|
| 26 | Las cuatro líneas del modelo | especificación, partial pooling |
| 27 | Modelos y codebases | efectos por modelo o por repo |
| 28 | Posterior predictive check | diagnósticos, ajuste |
| 29 | PPC por decisión | ajuste instrucción por instrucción |
| 30 | Especificación | priors, sampler, cadenas |
| 31 | Robustez | el refit solo-Qwen, r = 0,80 |
| 32 | Trabajo posterior | Gamage, Governance Decay |

## Preguntas probables

**¿Por qué no usaste un LLM como juez?**
Porque quería determinismo y reproducibilidad. Un juez introduce la varianza
del propio fenómeno que estoy midiendo. Tengo kappa checker-juez calculada en
el repo si les interesa.

**¿No es poco 244 observaciones?**
Sí, y por eso el modelo es jerárquico. Las decisiones con pocos datos salen con
intervalos anchos, que es exactamente lo que corresponde. El ranking de la
categoría "incierto" hay que tomarlo como preliminar.

**¿Los guardrails reales se comportan igual?**
No lo sé, y lo digo en limitaciones. Mi apuesta es que el mecanismo es el
mismo, pero probablemente sean más robustos que mis preferencias, porque viven
en posición cero y se refuerzan en entrenamiento.

**¿Por qué solo Qwen tiene control?**
Presupuesto. Los otros cuatro modelos corrieron solo la condición con
instrucción, para verificar que el patrón no fuera de una sola arquitectura.
*(Mostrá backup 31: refit solo-Qwen, r = 0,80, sigma beta 2,35 contra 2,11,
dos de los tres efectos positivos retienen el HDI sobre cero y parametrize
replica fuerte.)*

**¿Esto no es solo que los modelos chicos son peores?**
No. La retención no sube de 26B a 120B. Si fuera capacidad, el más grande
cumpliría más. *(Backup 27 si quieren ver los interceptos.)*

**¿Sabías del paper de omission vs commission?**
Sí, Gamage 2026. Encontró que las prohibiciones caen del 73% al 33% mientras
los requerimientos aguantan. Es heterogeneidad por tipo de instrucción, medida
después que esto, y va en la misma dirección. *(Backup 32.)*

## Cosas que NO decir

- No digas "el modelo deja de adherir". Decí "algo se pierde". En 8 de 12 el
  modelo ya cumplía solo, y si abrís fuerte te contradecís después.
- No prometas que mediste salvaguardas. Mediste preferencias de código.
- No digas que el efecto negativo desaparece al repuntuar. No está verificado
  con el dataset del paper, y en el refit solo-Qwen sigue dando negativo
  (aunque con intervalo más ancho). "Finding o artefacto" es la formulación
  honesta, y es la que está en la slide.
