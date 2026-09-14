# Gobierno, supervisión y contingencia

## Nivel de autonomía

El sistema opera con autonomía L2: analiza archivos, calcula indicadores y propone acciones. No modifica fuentes, no publica resultados y no ejecuta decisiones comerciales automáticamente.

## Responsables

| Situación | Responsable | Facultad |
|---|---|---|
| Operación normal | Brand Manager | Aprobar, rechazar o solicitar correcciones |
| Ausencia de Brand Manager | Marketing Manager | Suplencia temporal con registro obligatorio |
| Ausencia de ambos | Sin aprobador habilitado | Sólo generar y archivar; prohibido ejecutar |

## Contingencia ante ausencia de ambos responsables

1. La corrida se identifica como `pendiente_de_aprobacion`.
2. Los archivos de entrada, salida, integridad, reproducibilidad y consumo se conservan sin modificaciones.
3. No se envían recomendaciones a Comercial, Trade Marketing o Supply como instrucciones de ejecución.
4. No se aprueban inversiones, cambios de portfolio, distribución, promociones ni abastecimiento.
5. La corrida se incorpora a una cola de revisión con fecha, motivo y responsable esperado.
6. El primer responsable habilitado que regrese documenta en `revision_humana.md`: nombre, rol, fecha, decisión y correcciones.
7. La falta de respuesta nunca se interpreta como aprobación tácita.

## Escalamiento excepcional

Si existe una urgencia comercial, la corrida puede compartirse como información preliminar claramente rotulada, pero la decisión debe seguir el circuito de aprobación vigente de la compañía. El agente no designa nuevos aprobadores ni amplía su propia autonomía.

## Trazabilidad mínima

Toda corrida destinada a una decisión debe conservar entrada, salida, reporte de integridad, reporte de reproducibilidad, log de API y revisión humana. Si falta alguno, se considera evidencia incompleta.
