# Gobierno, supervisión y contingencia

## Nivel de autonomía

El sistema opera con autonomía L2: analiza archivos, calcula indicadores y propone acciones. No modifica fuentes, no publica resultados y no ejecuta decisiones comerciales automáticamente.

## Responsables

| Situación | Responsable | Autoridad concreta | Límites |
|---|---|---|---|
| Operación normal | Brand Manager | Aprobar o rechazar la validez analítica de la corrida; solicitar correcciones; autorizar que el reporte se comparta con Marketing, Comercial, Trade Marketing y Supply como recomendación | No puede tratar la recomendación del agente como autorización presupuestaria, alta o baja de SKU, modificación de forecast ni orden de abastecimiento |
| Ausencia de Brand Manager | Marketing Manager | Actuar como suplente; aprobar o rechazar la validez analítica; solicitar correcciones; autorizar la circulación del reporte dentro de planes y presupuestos ya aprobados | No puede ampliar el alcance del agente ni aprobar inversiones, cambios de portfolio o abastecimiento fuera del circuito corporativo correspondiente |
| Ausencia de ambos | Sin aprobador habilitado | Ninguna autoridad de aprobación; sólo se permite generar, registrar y archivar la corrida | Prohibido distribuirla como instrucción, ejecutar acciones o interpretar el silencio como aprobación |

## Matriz de decisión

| Decisión | Agente | Brand Manager | Marketing Manager suplente | Área funcional |
|---|---|---|---|---|
| Calcular indicadores y redactar recomendaciones | Ejecuta | Supervisa | Supervisa en suplencia | Informada |
| Aprobar la validez del análisis | Propone | Aprueba/rechaza | Aprueba/rechaza en ausencia | Informada |
| Compartir el reporte como recomendación | No autoriza | Autoriza | Autoriza en ausencia | Recibe |
| Ejecutar inversión o promoción | No ejecuta | Solicita por circuito vigente | Solicita por circuito vigente | Aprueba según política interna |
| Cambiar portfolio, forecast o abastecimiento | No ejecuta | Solicita por circuito vigente | Solicita por circuito vigente | Aprueba según política interna |

## Contingencia ante ausencia de ambos responsables

Si el responsable suplente —Marketing Manager— no está disponible, no se designa automáticamente un tercer aprobador. Se activa el siguiente protocolo:

1. La corrida se identifica como `pendiente_de_aprobacion`.
2. Los archivos de entrada, salida, integridad, reproducibilidad y consumo se conservan sin modificaciones.
3. No se envían recomendaciones a Comercial, Trade Marketing o Supply como instrucciones de ejecución.
4. No se aprueban inversiones, cambios de portfolio, distribución, promociones ni abastecimiento.
5. La corrida se incorpora a una cola de revisión con fecha, motivo y responsable esperado.
6. El primer responsable habilitado que regrese documenta en `revision_humana.md`: nombre, rol, fecha, decisión y correcciones.
7. La falta de respuesta nunca se interpreta como aprobación tácita.
8. Sólo puede intervenir otro aprobador si la Dirección lo designa previamente y por escrito. Sin esa designación, la decisión permanece bloqueada.
9. La designación excepcional debe indicar nombre, rol, corrida alcanzada y vigencia; se adjunta a `revision_humana.md` antes de cualquier circulación ejecutiva.

## Escalamiento excepcional

Si existe una urgencia comercial, la corrida puede compartirse como información preliminar claramente rotulada, pero la decisión debe seguir el circuito de aprobación vigente de la compañía. El agente no designa nuevos aprobadores ni amplía su propia autonomía.

## Trazabilidad mínima

Toda corrida destinada a una decisión debe conservar entrada, salida, reporte de integridad, reporte de reproducibilidad, log de API y revisión humana. Si falta alguno, se considera evidencia incompleta.
