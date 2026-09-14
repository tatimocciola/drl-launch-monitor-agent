# Reporte final de ejecución — corrida_05_reproduccion_corrida_01

- Fecha UTC: 2026-09-14T00:38:57.513788+00:00
- Archivos: entrada.csv.csv
- Fuentes: logyt
- Períodos: 202509, 202510, 202511, 202512, 202601, 202602, 202603, 202604, 202605, 202606, 202607, 202608

## Integridad de datos

Estado: **aprobado_con_advertencias**. Filas procesadas: 97.

Advertencias:
- Hay filas Logyt sin stock; no se evaluará cobertura para esas observaciones.

## Resultado de la hipótesis

Estado: **evidencia_insuficiente**. Confianza: **alto**.

La fuente disponible (Logyt) contiene únicamente índices de volumen y carece de métricas de rotación proxy y de las fuentes de sell-in, sell-out de distribuidores y Scentia necesarias para comprobar si la incorporación de los cuatro sabores acelera la rotación general.

## Hallazgos y acciones

1. Fuente logyt muestra picos máximos de volumen indexado en diciembre de 2025 (168.548 para 473 ml y 188.162 para 1 L) y mínimos en mayo de 2026 (65.173 y 68.785 respectivamente). — Acción propuesta: Ajustar la planificación de inventarios y abastecimiento en cadenas según la estacionalidad detectada.

## Consumo de API

- Modelo: gemini-3.5-flash-lite
- Tokens de entrada: 32678
- Tokens de salida: 5162
- Tokens totales: 37840
- Costo estimado a tarifa paga: USD 0.022708

## Supervisión

Requiere revisión humana: True.
Responsable final: Brand Manager.
Las recomendaciones no se ejecutan hasta recibir aprobación humana o aplicar el plan de contingencia documentado.