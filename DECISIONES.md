# Decisiones e iteraciones

Este documento registra la historia real de construcción del sistema, incluyendo cambios de alcance, resultados de las pruebas, errores y decisiones tomadas.

## Iteración 0 — Redefinición del proyecto

### Propuesta inicial

La primera propuesta buscaba analizar el scorecard completo del negocio RTD, generar alertas, incorporar información de e-commerce y RTD Market Watch, producir gráficos y anticipar el próximo cierre de Scentia mediante un nowcast.

### Problemas detectados

Al probar la propuesta observé que:

* El alcance era demasiado amplio para poder validar cada conclusión.
* El pronóstico de Scentia tenía un error histórico elevado.
* Algunos porcentajes resultaban difíciles de interpretar sin revisar los cálculos.
* Se mezclaban distintas fuentes, temporalidades y niveles de análisis.
* La solución era difícil de explicar y reproducir por una tercera persona.

### Decisión

Decidí comenzar nuevamente con un alcance más acotado. El nuevo sistema analizará únicamente el desempeño de los lanzamientos Green Apple y Red Berries en lata, comparándolos con otros sabores DR LEMON del mismo calibre.

El agente deberá distinguir evidencia, diagnóstico, limitaciones y acción sugerida. No realizará pronósticos de Scentia ni incorporará e-commerce en su primera versión.

### Motivo

Priorizo construir un sistema pequeño, funcional, comprensible y reproducible. Las funciones descartadas podrán considerarse como mejoras futuras una vez validado el núcleo del agente.

## Iteración 1 — Incorporación de fuentes reales y protección de datos

### Hallazgo

Al revisar los archivos reales observé que las fuentes tienen coberturas diferentes:

* Logyt contiene sell-out de cadenas, pero el archivo recibido no incluye stock.
* Sell-out de distribuidores contiene clientes compradores por área, pero no volumen.
* Scentia contiene volumen, distribución ponderada y distribución numérica hasta julio de 2026.
* Scentia contiene los cuatro sabores core en 1 L, pero no Green Apple ni Red Berries en 473 ml.

### Decisión sobre el alcance

Incorporé Scentia como cuarta fuente porque permite observar sell-out a consumidor final y distribución para los productos disponibles. El agente debe declarar las ausencias y no completar información por inferencia.

### Decisión sobre confidencialidad

El repositorio es público y los archivos originales contienen información comercial interna. Por ese motivo, las corridas publicadas utilizarán datos derivados de fuentes reales, pero anonimizados mediante índices.

Para cada fuente y calibre, el total DR LEMON del primer período comparable se expresa como índice 100. Los demás valores mantienen su relación respecto de esa base. Esta transformación conserva tendencias, variaciones y participaciones, pero evita publicar los volúmenes reales.

Los archivos originales no se incluyen en el repositorio. La Brand Manager conserva el acceso a las fuentes y valida que la transformación no altere las conclusiones.

## Iteración 2 — Validaciones y corrección de salidas

Durante las pruebas aparecieron errores concretos que obligaron a agregar controles automáticos. Entre ellos:

* Gemini respondió: `429 RESOURCE_EXHAUSTED ... You exceeded your current quota`, por lo que la interfaz dejó de mostrar el detalle técnico, informó que debía esperarse y evitó conservar una salida anterior como si fuera nueva.
* En una salida Scentia se afirmó `Contracción del consumo en ambos calibres` comparando enero con julio sin año anterior ni ajuste estacional. Se agregó una validación que impide calificar ese movimiento como caída o tendencia.
* Una salida indicó que Scentia carecía de datos para calcular rotación. La regla fue corregida: en Scentia la rotación se calcula como volumen dividido por ND para la misma combinación de período, área, sabor y calibre.
* Una acción propuso abastecimiento desde Logyt aunque esa corrida no incluía stock. La revisión humana rechazó la acción y documentó que volumen por sí solo no prueba una necesidad de abastecimiento.

## Iteración 3 — Evidencia técnica y trazabilidad económica

La evaluación externa otorgó 96,25 puntos y señaló que el costo estaba calculado, pero faltaba un artefacto que probara el consumo real. Se decidió:

* convertir los controles de entrada en un reporte `integridad_datos.json`;
* guardar `log_consumo_api.json` con los tokens devueltos por `usage_metadata`;
* generar automáticamente `reporte_ejecucion.md`;
* permitir descargar los artefactos juntos desde Streamlit;
* mantener la arquitectura original para no comprometer la reproducibilidad de las cuatro corridas ya verificadas.

## Plan de contingencia de aprobación

La Brand Manager es responsable primaria. Ante su ausencia, la aprobación se deriva al Marketing Manager, quien debe dejar constancia de su nombre, fecha y decisión en la revisión humana. Si ambas personas están ausentes, el sistema puede producir y archivar el análisis, pero ninguna recomendación se ejecuta hasta contar con aprobación. No existe aprobación automática por silencio.

## Iteración 4 — Validación cruzada y reproducibilidad

Una segunda evaluación recomendó detectar incompatibilidades entre fuentes y generar evidencia técnica de reconstrucción. Se incorporaron controles de unidades dentro de cada fuente, unidades incompatibles sobre claves coincidentes y falta de períodos comunes. También se agregó `reporte_reproducibilidad.json`, con hashes SHA-256 de las entradas y prompts, versiones de Python y pandas, modelo utilizado y resultado de integridad.

Se creó `VERSIONES.md` para navegar el historial real de los prompts y `GOBIERNO.md` para formalizar qué ocurre si faltan la responsable primaria y su suplente.

El log original de tokens de la corrida 01 no puede reconstruirse porque `usage_metadata` no se guardó en ese momento. No se inventa ni se presenta una estimación como medición histórica. La medición directa se demostrará mediante una nueva corrida reproducible con el código instrumentado.
