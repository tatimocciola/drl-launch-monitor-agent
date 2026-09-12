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
