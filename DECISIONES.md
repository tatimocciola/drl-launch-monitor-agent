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
