# Instancia II — Revisión de Literatura (Diseño)

**Fecha:** 2026-05-03
**Entrega:** 2026-05-07 (formato PPT)
**Tiempo de exposición:** 5 minutos máximo

## Objetivo

Cumplir la consigna de Instancia II: revisión crítica de la literatura sobre Context Rot y mitigación de instruction decay en LLMs, con identificación de vacancias y orientación al proyecto final.

## Restricciones

- 5 minutos duros (en Instancia I se pasó de tiempo).
- Formato de entrega: PPT.
- Consigna pide foco en literatura, no en trabajo propio.
- El paper JAIIO 2026 ("Not All Instructions Are Forgotten Equal") está sometido pero no aceptado. Aparece solo como bisagra al final, en el slot de "orientación del proyecto final".
- Tono: comparativo y crítico, no narrativo.

## Estructura (7 slides)

| # | Slide | Tiempo |
|---|-------|--------|
| 1 | Título | 10 s |
| 2 | Delimitación del problema | 30 s |
| 3 | Eje 1: Medición del fenómeno | 60 s |
| 4 | Eje 2: Mecanismo | 50 s |
| 5 | Eje 3: Mitigaciones existentes (tabla comparativa) | 60 s |
| 6 | Eje 4 + vacancia (Bayesian framing y BKT) | 50 s |
| 7 | Orientación: insight propio del JAIIO | 40 s |

Total: 300 s exactos. Margen cero. Hacer dry-run cronometrado.

## Contenido por slide

### Slide 1 — Título
- "Análisis de soluciones existentes: Context Rot en LLMs"
- Nombre, materia, Instancia II.

### Slide 2 — Delimitación
- Definir Context Rot en una frase: pérdida de adherencia a instrucciones a medida que la conversación crece.
- Recordar que se introdujo en Instancia I.
- Acotar la revisión: papers que (a) miden el fenómeno, (b) explican el mecanismo, (c) proponen mitigación.

### Slide 3 — Eje 1: Medición del fenómeno
Tabla simple, 3 filas:
- Laban et al. 2025 → 39% drop, 15 modelos, multi-turn
- He et al. 2024 (Multi-IF) → 87.7% → 70.7% en 3 turnos
- Chroma 2025 (industria) → 18/18 modelos frontera

Síntesis: los tres reportan métricas agregadas. Ninguno desagrega por tipo de instrucción.

### Slide 4 — Eje 2: Mecanismo
- Liu et al. 2024: U-curve, info en el medio se pierde. Plot de pgfplots reciclado de Instancia I.
- Mu et al. 2025: saturación. Más reglas → menos adherencia a cada una.

Síntesis: la atención no se reparte uniforme — ni por posición (Liu) ni por cantidad (Mu).

### Slide 5 — Eje 3: Mitigaciones (tabla comparativa)
Tabla de 4 filas × 4 columnas:

| Método | Idea | Costo | Limitación |
|---|---|---|---|
| Jerarquía de instrucciones (Wallace 2024, OpenAI) | system > user, prioridad estática | Cero extra | No aborda decay temporal |
| Repetir prompt cada turno | Re-inyectar todo | N× tokens | Saturación (Mu 2025) |
| Duplicar prompt (Google 2025) | Instrucciones 2× | 2× tokens | Refuerzo uniforme |
| Recordatorios periódicos (Dongre 2025) | Re-inyectar cada k turnos | k-dependiente | Mismo refuerzo a todas |

Conclusión: ninguna decide qué reforzar.

### Slide 6 — Eje 4 + vacancia
- Zhang et al. 2025: LLMs como filtros bayesianos descontados (γ < 1).
- Corbett & Anderson 1994: BKT, 30 años en educación, estima mastery por concepto.
- Vacancia detectada: ningún paper aplicó BKT a compliance de LLMs. Más importante: ningún paper midió si el decay es heterogéneo entre instrucciones — premisa que un sistema BKT necesitaría.

### Slide 7 — Orientación + insight JAIIO
- Antes de proponer un sistema BKT selectivo, había que verificar el supuesto de heterogeneidad.
- Estudio empírico propio: 28 conversaciones, 244 observaciones, 5 modelos, modelo logístico ordinal bayesiano.
- Resultado: σ_β = 2.11, HDI [1.06, 3.28] → la heterogeneidad existe.
- Próximo paso del proyecto final: construir el sistema BKT con presupuesto fijo de tokens y testear contra refuerzo uniforme.
- Mencionar honestamente: paper sometido a JAIIO 2026, no aceptado todavía.

## Papers citados (9 total)

**Eje 1:** Laban et al. 2025, He et al. 2024, Chroma 2025 (industria)
**Eje 2:** Liu et al. 2024, Mu et al. 2025
**Eje 3:** Wallace et al. 2024, Google Research 2025, Dongre et al. 2025
**Eje 4:** Zhang et al. 2025, Corbett & Anderson 1994

Excluidos del corte de Instancia I: Du et al. 2025 (redundante con Laban), Leviathan et al. 2025 (redundante con Google), Lindsey et al. 2025 y Ameisen et al. 2025 (interpretabilidad — contexto del campo, no método para mitigar). Anthropic (2025) Activation Oracles también fuera por la misma razón.

## Pipeline de build

LaTeX/Beamer → PDF → image-PPT vía `pdf2pptx`.

```bash
# Setup una vez
git clone https://github.com/ashafaei/pdf2pptx.git tools/pdf2pptx
pip install -r tools/pdf2pptx/requirements.txt

# Build
xelatex presentacion-instancia2.tex
xelatex presentacion-instancia2.tex
./tools/pdf2pptx/pdf2pptx.sh presentacion-instancia2.pdf
# Output: presentacion-instancia2.pdf.pptx
```

Justificación: las herramientas "PPT editable" (Sharayeh, beamer2pptx) rompen pgfplots y tablas con colores custom. Image-PPT preserva la estética exacta de Beamer y produce un .pptx legítimo. Trade-off aceptado: no editable.

## Estética

- Theme: metropolis default (fondo claro). Quitar los `setbeamercolor` que en `presentacion-nodo.tex` pintan `darkbg` y `offwhite` — sin esas líneas, metropolis es blanco/gris.
- Razón del cambio: diferenciar visualmente Instancia I (pitch narrativo) de Instancia II (lit review). El fondo claro encaja con género académico/comparativo.
- Mantener fontspec y estructura de frames de `presentacion-nodo.tex`.
- Title slide: sin imagen de fondo. Solo texto sobre fondo claro, centrado.
- Color de acento: un único color para énfasis (rojo o naranja sobrio, p. ej. `#A43F2A`). Sin paleta múltiple.

## Archivos

- Fuente: `presentacion-instancia2.tex` en raíz del repo.
- Build: agregar target `instancia2-pptx` en un `Makefile` nuevo en raíz, que corra xelatex 2× y luego `pdf2pptx.sh`.
- Tools: `git clone https://github.com/ashafaei/pdf2pptx.git tools/pdf2pptx` (ignorado por git vía `.gitignore`).
- Output: `presentacion-instancia2.pdf` (intermedio) y `presentacion-instancia2.pdf.pptx` (entregable).

## Riesgos

1. **Reloj.** Es fácil pasarse de 5 min con 7 slides. Mitigación: hacer un dry-run cronometrado antes del 7/5.
2. **Slide 7 puede leerse como auto-promoción.** Mitigación: redacción explícita de que el JAIIO es trabajo en revisión, no resultado validado, y que motiva el proyecto final.
3. **Image-PPT no editable.** Riesgo si la cátedra exige slides editables. Mitigación: si rechazan, fallback a Google Slides nativo (re-trabajo: ~2 h).

## Fuera de alcance

- Reescribir el guion de Instancia I.
- Construir el sistema BKT real (eso es Instancia III / proyecto final).
- Animaciones o transiciones más allá de `\pause`.
