# Análisis económico y consumo de API

## Modelo elegido

El sistema usa `gemini-3.5-flash-lite` porque el trabajo principal consiste en interpretar indicadores ya normalizados y devolver un JSON bajo esquema. Se priorizan baja latencia y costo, ya que las validaciones determinísticas y los cálculos se resuelven en Python antes de invocar el modelo.

Como alternativa se consideró `gemini-3.5-flash`. Su mayor capacidad no resulta necesaria para el alcance actual y su tarifa de referencia es superior. Flash-Lite mantiene una salida estructurada suficiente y reserva la revisión de decisiones para una persona.

## Tarifas de referencia

Consulta: 13 de septiembre de 2026.

| Modelo | Entrada por 1 M tokens | Salida por 1 M tokens |
|---|---:|---:|
| Gemini 3.5 Flash-Lite | USD 0,30 | USD 2,50 |
| Gemini 3.5 Flash | USD 0,75 | USD 4,50 |

Fuente oficial: https://ai.google.dev/gemini-api/docs/pricing

## Medición

Cada llamada captura `prompt_token_count`, `candidates_token_count` y `total_token_count` desde `usage_metadata` de Gemini. La evidencia se guarda en `log_consumo_api.json`; si existe una segunda llamada correctiva, Streamlit suma ambas.

La fórmula es:

`costo = tokens_entrada / 1.000.000 × tarifa_entrada + tokens_salida / 1.000.000 × tarifa_salida`

El cálculo informa el equivalente a tarifa paga aunque la ejecución utilice el nivel gratuito.

## Proyección operativa

La proyección utiliza el costo real de una corrida registrada:

* Escenario base: 2 corridas por mes o 24 por año.
* Escenario intensivo: 8 corridas por mes o 96 por año.
* Costo mensual base: `costo_por_corrida × 2`.
* Costo anual base: `costo_por_corrida × 24`.
* Costo mensual intensivo: `costo_por_corrida × 8`.
* Costo anual intensivo: `costo_por_corrida × 96`.

No se monetiza el ahorro de tiempo humano porque todavía no se midió una línea de base confiable. Esta exclusión evita inventar un beneficio económico.

## Controles de costo

* Se envían registros normalizados, no archivos originales completos.
* La corrección automática usa el borrador y las infracciones, no repite toda la base.
* Se registra el número real de llamadas para que un reintento no quede oculto.
* Ante un error 429 no se reutiliza una salida anterior como si fuera nueva.

## Medición real — corrida 05

La reproducción técnica de la corrida 01 registró dos llamadas a `gemini-3.5-flash-lite`:

| Métrica | Resultado |
|---|---:|
| Tokens de entrada | 32.678 |
| Tokens de salida | 5.162 |
| Tokens totales | 37.840 |
| Costo equivalente por corrida | USD 0,022708 |

Proyección basada en esta medición:

| Escenario | Corridas | Costo mensual | Costo anual |
|---|---:|---:|---:|
| Base | 2 por mes | USD 0,045416 | USD 0,544992 |
| Intensivo | 8 por mes | USD 0,181664 | USD 2,179968 |

La medición se conserva en `corridas/corrida_05/log_consumo_api.json` y `log_consola_api.txt`. El costo efectivo puede ser cero bajo el nivel gratuito; la proyección utiliza tarifa paga para estimar una operación sostenible.
