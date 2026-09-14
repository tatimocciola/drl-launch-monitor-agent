# DRL Launch Monitor Agent

Trabajo final individual de la materia Programación de y con Agentes de IA — MBA UCEMA.

## Problema

El seguimiento de nuevos productos de DR LEMON combina información de distintas fuentes y períodos. Esto dificulta determinar rápidamente si un lanzamiento muestra una rotación competitiva, si está limitado por distribución o disponibilidad y dónde conviene actuar.

## Objetivo inicial

Construir un agente simple que analice información real de Green Apple y Red Berries en lata, los compare con otros sabores DR LEMON del mismo calibre y genere conclusiones estructuradas para revisión humana.

## Alcance

El agente utilizará archivos tabulares como herramienta de entrada y devolverá:

* Validación, rechazo o indeterminación de la hipótesis analizada.
* Evidencia utilizada.
* Diagnóstico.
* Acción sugerida.
* Responsable y KPI.
* Limitaciones de la información.
* Nivel de confianza.
* Indicación de revisión humana obligatoria.

El agente no modificará sistemas internos ni ejecutará decisiones comerciales automáticamente.

## Cómo ejecutarlo

### Streamlit

1. Instalá las dependencias con `py -m pip install -r requirements.txt`.
2. Configurá `GEMINI_API_KEY` como secreto de Streamlit o variable de entorno.
3. Ejecutá `py -m streamlit run app.py`.
4. Cargá uno o más CSV normalizados o un ZIP Scentia.
5. Ejecutá el análisis y descargá el paquete completo de evidencia.

### Línea de comandos

```bash
python ejecutar_agente.py datos/plantilla_entrada.csv --corrida corrida_05 --salida salida/corrida_05
```

## Artefactos automáticos por corrida

El sistema genera:

* `salida.json`: resultado estructurado del agente.
* `integridad_datos.json`: controles ejecutados, errores bloqueantes, advertencias y cobertura de la entrada.
* `log_consumo_api.json`: modelo, tokens medidos mediante `usage_metadata`, tarifas de referencia y costo estimado.
* `reporte_ejecucion.md`: síntesis automática de entrada, integridad, conclusión, acciones, consumo y supervisión.

La aplicación Streamlit entrega estos cuatro archivos dentro de un único ZIP.

## Validaciones de integridad

Antes de invocar el modelo se controlan columnas obligatorias, archivo vacío, dominios admitidos, período `AAAAMM`, valores negativos, porcentajes fuera de rango, coherencia entre anonimización y unidad, compatibilidad de bases índice, claves duplicadas y disponibilidad de campos necesarios para cada métrica. Los errores bloqueantes impiden la corrida; las advertencias quedan registradas para revisión humana.

## Supervisión y contingencia

La autonomía es L2: el agente analiza y recomienda, pero no ejecuta decisiones. La Brand Manager es la responsable primaria. Si está ausente, revisa el Marketing Manager y documenta nombre, fecha y decisión. Si ambos están ausentes, la corrida queda archivada y pendiente de aprobación; ninguna recomendación comercial, de portfolio, inversión, distribución o abastecimiento se ejecuta automáticamente.

## Análisis económico

Se utiliza `gemini-3.5-flash-lite` por su relación entre costo, velocidad y capacidad para producir JSON estructurado. La tarifa paga de referencia consultada el 13 de septiembre de 2026 es USD 0,30 por millón de tokens de entrada y USD 2,50 por millón de tokens de salida. El costo de cada corrida se calcula con el consumo real devuelto por la API:

`costo = tokens_entrada / 1.000.000 × 0,30 + tokens_salida / 1.000.000 × 2,50`

El nivel gratuito puede producir costo efectivo cero; se informa igualmente el equivalente a tarifa paga para estimar una operación futura. La proyección mensual se obtiene multiplicando el costo medido por la cantidad esperada de corridas: escenario base de 2 corridas mensuales y escenario intensivo de 8. Las cifras se actualizan con el log real de cada ejecución. Fuente: https://ai.google.dev/gemini-api/docs/pricing

## Corridas documentadas

El directorio `corridas/` contiene cuatro pruebas verificables con entrada, salida y revisión humana: una corrida inicial, una Scentia, una Logyt con datos reales y una multifuente. Las limitaciones y correcciones se mantienen visibles como parte del proceso.
