# Diseño de slides: charla JAIIO/ASAID 2026 (paper #249)

Presentación oral de "Not All Instructions Are Forgotten Equal" en el 55 JAIIO
(10 al 13 de agosto de 2026, UTN-FRLP, La Plata). Este documento fija la
estructura de la charla, qué contenido va en cada slide y qué figuras hay que
regenerar. No contiene el texto final de las slides, que se escribe después
sobre esta base.

## Restricciones

- Slot oficial de 20 minutos, de los cuales la organización sugiere 17 de
  exposición. Planificamos 13 minutos de contenido hablado, de modo que el
  margen absorba preguntas y cambio de orador, siguiendo el formato real de
  los orals de ICML/NeurIPS (15 minutos totales incluyendo transición).
- Idioma: castellano, con términos técnicos en inglés donde suene natural
  (guardrail, ordered logit, partial pooling, forest plot).
- Todo el contenido sale del paper camera-ready (`paper/paper.tex` y
  `paper/figures/`). El material de la extensión v2 (`extended.tex`,
  `methods.tex`, `report-figures/v6/`, `analysis-out-*`) queda excluido.
- Audiencia: académicos y profesionales de IA aplicada, hispanohablantes, no
  necesariamente familiarizados con seguridad de agentes. La apertura no usa
  jerga de alignment y arranca desde un problema técnico concreto.

## Mensaje central

Un solo takeaway, repetido tres veces (forecast, resultados, cierre): la
retención de instrucciones es muy despareja entre instrucciones, de modo que
el promedio agregado esconde cuál regla se perdió, y solo 3 de 12 se
benefician de ser repetidas. La implicación de seguridad es que un agente
desplegado necesita monitoreo por instrucción.

Los resultados son el centro de la charla (5 a 6 minutos), whereas el modelo
estadístico se comprime a una slide, siguiendo la regla de elegir modelo o
resultados y reducir el otro a su mínimo.

## Esqueleto (12 slides de contenido)

Los tiempos por slide suman unos 15 minutos en el peor caso. El ensayo
cronometrado ajusta el ritmo, y los recortes marcados (R1 y R4) llevan la
charla a los 13 minutos objetivo si hace falta.

1. **Título** (30s). Nombre, afiliación (UNSAM), repo al pie.
2. **Apertura 1** (1 min). Los agentes corren muchos turnos llamando
   herramientas sin supervisión por paso, whereas sus instrucciones,
   incluidas las salvaguardas, se dan una sola vez al principio y deben valer
   toda la corrida.
3. **Apertura 2** (1,5 min). La adherencia se degrada a medida que el
   contexto crece (caída promedio documentada del 39%, atención en U), y los
   estudios existentes reportan adherencia promedio sobre conjuntos de
   instrucciones, que no identifica cuál instrucción cayó. La frase es la del
   paper, acotada a la literatura citada, porque el universal "todo lo medido
   hasta ahora" es indefendible frente al trabajo de 2026 (ver backups).
4. **Forecast** (1 min). La pregunta (medir retención instrucción por
   instrucción) y el hallazgo adelantado (retención muy despareja, con
   efectos de −2,4 a +5,4 en log-odds, y solo 3 de 12 instrucciones se
   benefician de la repetición). Estilo Mark Hill: el resultado se anuncia al
   principio y la charla lo gana.
5. **Método, protocolo** (1,5 min). Sesiones de código simuladas de 25 turnos
   sobre tres codebases reales (Bambi 98K, ArviZ 160K, PyMC 203K tokens de
   presión de contexto), 12 preferencias plantadas como pedidos casuales (6
   tempranas en turnos 1 a 7, 6 tardías en 14 a 19), turnos de prueba 20 a
   25, checkers determinísticos con escala ordinal 0 a 3. Acá conviene un
   diagrama de la línea de tiempo de la conversación en lugar de texto.
6. **Método, modelo** (1 min). Regresión logística ordenada con efectos
   jerárquicos por tipo de decisión, donde σ_β mide cuánto varían las
   instrucciones entre sí y el partial pooling protege contra los pocos datos
   por celda. A lo sumo la ecuación del predictor lineal, sin más fórmulas.
   Escala: 28 conversaciones, 244 observaciones, 5 modelos.
7. **R1, datos crudos** (1 min). `raw_retention_landscape` regenerada con
   estilo de slides. La historia completa se ve antes de cualquier Bayes:
   tres instrucciones con baseline cero que saltan al ser dichas, ocho que ya
   se cumplen por defecto, y una que baja al ser dicha. Nota de honestidad
   si preguntan: el baseline es solo Qwen, el treatment agrupa los 5 modelos.
8. **R2, forest plot** (2,5 a 3 min). La slide central, con tres builds
   progresivos sobre `treatment_effects_forest`: primero las tres con HDI
   sobre cero (`testing_parametrize` β=5,4 con baseline 0), después las ocho
   cuyo HDI cruza cero porque ya se cumplen, y por último `deps_no_new`
   (β=−2,4), sospechada de artefacto de medición del checker, caveat que se
   dice explícito porque compra credibilidad.
9. **R3, política de refuerzo** (2 min). `reinforcement_policy` (la figura,
   no la tabla): ganancia ΔP(score≥2) por instrucción, y la lectura práctica
   de que repetir todo desperdicia tokens en 9 de 12. Cierra con la
   salvedad del paper: ganancia baja no licencia descartar una regla de
   seguridad.
10. **R4, invarianza** (1 min). Sin efecto detectable por modelo ni codebase
    (σ≈0,3), y la retención no sube de 26B a 120B, de modo que la
    heterogeneidad no es capacidad disfrazada. Slide liviana, sin figura;
    puede fundirse con R3 si el ensayo muestra que falta tiempo.
11. **Discusión** (1,5 min). Las preferencias son un stand-in de
    salvaguardas, porque ambas son instrucciones dichas una vez que compiten
    por atención. Como la seguridad es conjuntiva, el agregado puede verse
    bien mientras la regla que importa ya cayó, de donde sale la necesidad
    de monitoreo por instrucción y la dirección BKT.
12. **Conclusión** (1 min). Las tres contribuciones en una oración cada una,
    el repo (github.com/korentomas/not-all-instructions), gracias.

## Backups (después de la conclusión, munición para preguntas)

- PPC y convergencia (`posterior_predictive_check`; cero divergencias,
  R̂≤1.01, ESS mín. 1311).
- `ppc_per_decision`, para preguntas sobre validez de los checkers.
- Especificación completa del modelo y priors.
- Detalle del artefacto en `deps_no_new` (el checker cuenta cualquier import
  como nuevo, incluidos los ya presentes).
- Elección de las 12 preferencias y de los 3 codebases.
- Robustness checks (sección 6.2 del paper).
- Related work 2026: Omission/Commission (arXiv 2604.20911, heterogeneidad
  por categoría de restricción, corrobora la dirección pero no estima
  efectos por instrucción individual), Governance Decay (2606.22528),
  HANDBOOK.md (2607.25398). Respuesta preparada: el trabajo posterior
  confirma que el promedio esconde fallas, whereas este paper baja la
  resolución hasta la instrucción individual.

## Trabajo sobre figuras

Las cuatro figuras del paper están en tamaño y tipografía de página A4, de
modo que hay que regenerarlas para proyección (fuentes grandes, aspecto de
slide, fondo compatible con el template que se elija). Los scripts existen y
comparten módulo de estilo (commit `9b3d2e6`). `raw_retention_landscape`
solo existe como PNG con estilo matplotlib default, así que se regenera con
el mismo módulo. El forest plot necesita además las tres variantes de
resaltado para los builds de la slide 8.

## Reglas de redacción de las slides

- Títulos estilo humano pre-2020 (patrón Devlin/Kaiser): etiquetas cortas de
  dos a cuatro palabras ("Datos crudos", "Efectos por instrucción"), repetidas
  cuando un tema ocupa varias slides. La afirmación va al cuerpo como línea
  final en negrita (clase takeaway), que es donde esos decks ponen el remate.
- Una idea por slide, gráficos sobre tablas, mínimo texto.
- Sin outline slide y sin slide de literatura (las citas van inline donde
  se usan).
- Aplican las preferencias de prosa de Tomás: oraciones completas conectadas,
  conectores en lugar de dos puntos discrecionales, cero em-dashes, sin
  estructuras retóricas de LLM (pregunta gancho, setup y remate, contraste
  armado).

## Ensayo

Práctica en voz alta y cronometrada, cinco pasadas como mínimo. Las slides
R1 y R4 quedan marcadas como recortables si el tiempo no alcanza. Aim:
terminar en 13 minutos.
