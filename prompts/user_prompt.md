# User prompt — Análisis de portfolio DR LEMON

Analizá los datos entregados aplicando todas las reglas del system prompt.

## Identificación de la corrida

* ID: `{corrida_id}`
* Fecha de ejecución: `{fecha_ejecucion}`
* Archivo analizado: `{nombre_archivo}`

## Datos procesados por la herramienta

```json
{datos_json}
```

## Tarea

1. Verificá la calidad y suficiencia de los datos.
2. Identificá las fuentes, los períodos y las temporalidades disponibles.
3. Analizá primero el desempeño general de DR LEMON en 473 ml y 1 L.
4. Analizá después el rol de Vodka, Limón, Green Apple y Red Berries dentro de cada calibre.
5. Evaluá si completar el portfolio con los cuatro sabores se relaciona con una aceleración de la rotación proxy general.
6. Identificá diferencias entre sell-in, sell-out de distribuidores y Logyt.
7. Separá evidencia, interpretación, información faltante y acción sugerida.
8. Determiná si la hipótesis queda validada, parcialmente validada, rechazada o con evidencia insuficiente.
9. Indicá qué debe revisar una persona antes de utilizar el resultado.

## Formato obligatorio

Respondé exclusivamente con un JSON válido. No agregues texto antes ni después.

Utilizá exactamente esta estructura:

```json
{
  "corrida": {
    "id": "",
    "fecha_ejecucion": "",
    "archivo": "",
    "fuentes_analizadas": [],
    "periodos_analizados": [],
    "temporalidades": []
  },
  "calidad_datos": {
    "estado": "suficiente|parcial|insuficiente",
    "problemas_detectados": [],
    "datos_faltantes_relevantes": []
  },
  "resultado_hipotesis": {
    "estado": "validada|parcialmente_validada|rechazada|evidencia_insuficiente",
    "justificacion": "",
    "nivel_confianza": "alto|medio|bajo"
  },
  "desempeno_por_calibre": [
    {
      "calibre": "473 ml|1 L",
      "evidencia": [],
      "interpretacion": "",
      "limitaciones": []
    }
  ],
  "rol_por_sabor": [
    {
      "sabor": "Vodka|Limón|Green Apple|Red Berries",
      "calibre": "473 ml|1 L",
      "evidencia": [],
      "interpretacion": "",
      "dato_faltante": ""
    }
  ],
  "hallazgos_priorizados": [
    {
      "prioridad": 1,
      "nivel": "total_marca|calibre|sabor|area",
      "fuente": "",
      "periodo": "",
      "temporalidad": "",
      "evidencia": "",
      "interpretacion": "",
      "accion_sugerida": "",
      "responsable_sugerido": "Marketing|Comercial|Trade Marketing|Supply",
      "kpi_seguimiento": "",
      "confianza": "alta|media|baja"
    }
  ],
  ],
  "dashboard": {
    "hallazgos": [
      {
        "titulo": "",
        "evidencia": "",
        "fuente": "",
        "periodo": "",
        "interpretacion": "",
        "confianza": "alta|media|baja"
      }
    ],
    "oportunidades": [
      {
        "titulo": "",
        "evidencia": "",
        "fuente": "",
        "periodo": "",
        "interpretacion": "",
        "confianza": "alta|media|baja"
      }
    ],
    "debilidades": [
      {
        "titulo": "",
        "evidencia": "",
        "fuente": "",
        "periodo": "",
        "interpretacion": "",
        "confianza": "alta|media|baja"
      }
    ],
    "amenazas": [
      {
        "titulo": "",
        "evidencia": "",
        "fuente": "",
        "periodo": "",
        "interpretacion": "",
        "confianza": "alta|media|baja"
      }
    ]
  },
 "contradicciones_entre_fuentes": [],
  "revision_humana": {
    "requiere_revision_humana": true,
    "puntos_a_revisar": [],
    "responsable_final": "Brand Manager"
  }
}
```

## Límites

* Incluí como máximo cinco hallazgos priorizados.
* Incluí como máximo tres elementos en cada categoría del dashboard.
* Devolvé una lista vacía cuando una categoría no tenga evidencia suficiente.
* No completes con cero los datos ausentes.
* No calcules indicadores que no tengan denominador válido.
* No afirmes disponibilidad por punto de venta a partir del stock agregado.
* No atribuyas consumo final a una fuente que no lo mide.
* Conservá las unidades originales de cada indicador.
