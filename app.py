import json
import os
from datetime import datetime, timezone

import streamlit as st
from google import genai
from google.genai import types

from ejecutar_agente import RESPONSE_SCHEMA, leer_prompt, validar_y_preparar
from preparar_scentia import normalizar_scentia_zip


st.set_page_config(page_title="DRL Core Portfolio Agent", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
    div[data-testid="stMarkdownContainer"] div.drl-card,
    div[data-testid="stMarkdownContainer"] div.drl-card * { color: #111827 !important; }
    div.drl-card small { color: #4B5563 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


def detectar_infracciones(resultado, df):
    infracciones = []
    fuentes = set(df["fuente"].dropna().astype(str))
    periodos = df["periodo"].dropna().astype(str).tolist()
    solo_un_anio = periodos and len({p[:4] for p in periodos}) == 1

    textos_temporales = []
    for bloque in resultado.get("desempeno_por_calibre", []):
        textos_temporales.append(bloque.get("interpretacion", ""))
    for bloque in resultado.get("hallazgos_priorizados", []):
        textos_temporales.extend([bloque.get("evidencia", ""), bloque.get("interpretacion", "")])
    for categoria in resultado.get("dashboard", {}).values():
        for bloque in categoria:
            textos_temporales.extend([
                bloque.get("titulo", ""), bloque.get("evidencia", ""),
                bloque.get("interpretacion", ""),
            ])
    texto_temporal = " ".join(textos_temporales).lower()
    terminos_tendencia = ["caída", "caida", "contracción", "contraccion", "disminución", "disminucion", "decrece", "decreciente"]
    if fuentes == {"scentia"} and solo_un_anio and any(t in texto_temporal for t in terminos_tendencia):
        infracciones.append(
            "No califiques el movimiento enero-julio como caída, contracción, disminución o tendencia: no hay comparación interanual ni desestacionalizada."
        )

    problemas = " ".join(resultado.get("calidad_datos", {}).get("problemas_detectados", [])).lower()
    if "anonimiz" in problemas:
        infracciones.append(
            "No clasifiques la anonimización mediante índices como problema de calidad; informala únicamente como limitación para magnitudes absolutas."
        )

    dashboard_riesgos = json.dumps(
        {k: resultado.get("dashboard", {}).get(k, []) for k in ["oportunidades", "debilidades", "amenazas"]},
        ensure_ascii=False,
    ).lower()
    if "473" in dashboard_riesgos and ("green apple" in dashboard_riesgos or "red berries" in dashboard_riesgos):
        infracciones.append(
            "No clasifiques la falta conocida de Green Apple o Red Berries 473 ml en Scentia como oportunidad, debilidad o amenaza."
        )

    responsables = {"marketing", "comercial", "trade marketing", "supply"}
    if any(
        h.get("accion_sugerida", "").strip().lower() in responsables
        for h in resultado.get("hallazgos_priorizados", [])
    ):
        infracciones.append("Cada acción sugerida debe comenzar con un verbo y ser distinta del nombre del responsable.")

    if fuentes == {"scentia"} and df["rotacion_proxy"].notna().any():
        evidencia_rotacion = " ".join(
            " ".join(r.get("evidencia", [])) for r in resultado.get("rol_por_sabor", [])
        ).lower()
        if "rotaci" not in evidencia_rotacion:
            infracciones.append(
                "Incluí evidencia cuantitativa de la evolución del índice de rotación Scentia (volumen/ND) para combinaciones comparables."
            )
    return infracciones


def mostrar_tarjetas(elementos, color):
    if not elementos:
        st.info("No se identificaron elementos con evidencia suficiente.")
        return
    for item in elementos:
        st.markdown(
            f"""
            <div class="drl-card" style="border-left: 5px solid {color}; padding: 12px 16px; margin: 10px 0;
                        background: #ffffff; color: #111827; border-radius: 6px; box-shadow: 0 1px 4px #00000018;">
              <strong>{item.get('titulo', 'Sin título')}</strong><br>
              <small>{item.get('fuente', '')} · {item.get('periodo', '')}</small><br>
              <b>Evidencia:</b> {item.get('evidencia', '')}<br>
              <b>Interpretación:</b> {item.get('interpretacion', '')}<br>
              <b>Confianza:</b> {item.get('confianza', '')}
            </div>
            """,
            unsafe_allow_html=True,
        )


def calcular_metricas_ejecucion(responses, modelo):
    usos = [getattr(response, "usage_metadata", None) for response in responses]
    usos = [uso for uso in usos if uso is not None]
    tokens_entrada = sum(int(getattr(uso, "prompt_token_count", 0) or 0) for uso in usos)
    tokens_salida = sum(int(getattr(uso, "candidates_token_count", 0) or 0) for uso in usos)
    tokens_totales = sum(int(getattr(uso, "total_token_count", 0) or 0) for uso in usos)
    tarifa_entrada = 0.30
    tarifa_salida = 2.50
    costo = tokens_entrada / 1_000_000 * tarifa_entrada + tokens_salida / 1_000_000 * tarifa_salida
    return {
        "modelo": modelo,
        "llamadas_modelo": len(usos),
        "tokens_entrada": tokens_entrada,
        "tokens_salida": tokens_salida,
        "tokens_totales": tokens_totales,
        "tarifa_entrada_usd_por_millon": tarifa_entrada,
        "tarifa_salida_usd_por_millon": tarifa_salida,
        "costo_estimado_usd": round(costo, 6),
        "tarifa_referencia_fecha": "2026-09-13",
        "tarifa_referencia_url": "https://ai.google.dev/gemini-api/docs/pricing",
    }


st.title("DRL Core Portfolio Agent")
st.caption("Evaluación supervisada del rol de Vodka, Limón, Green Apple y Red Berries en 473 ml y 1 L")

with st.sidebar:
    st.header("Nueva corrida")
    archivos = st.file_uploader(
        "Fuentes para analizar (CSV normalizados o ZIP Scentia)",
        type=["csv", "zip"],
        accept_multiple_files=True,
    )
    corrida_id = st.text_input("ID de corrida", value="corrida_01")
    modelo = st.text_input("Modelo", value="gemini-3.5-flash-lite")
    clave_configurada = os.getenv("GEMINI_API_KEY", "")
    if clave_configurada:
        clave = clave_configurada
        st.success("API de Gemini configurada")
    else:
        clave = st.text_input("Gemini API key", type="password")
    ejecutar = st.button("Ejecutar análisis", type="primary", use_container_width=True)

if ejecutar:
    st.session_state.pop("resultado", None)
    st.session_state.pop("controles_salida", None)
    st.session_state.pop("tokens", None)
    st.session_state.pop("metricas_ejecucion", None)
    if not archivos:
        st.error("Seleccioná al menos un CSV normalizado o un ZIP de Scentia.")
        st.stop()
    if not clave:
        st.error("Ingresá la Gemini API key. La aplicación no la guarda.")
        st.stop()

    try:
        entradas = []
        nombres = []
        for archivo in archivos:
            try:
                if archivo.name.lower().endswith(".zip"):
                    entrada = normalizar_scentia_zip(archivo.getvalue())
                else:
                    entrada = archivo
                df_archivo, _ = validar_y_preparar(entrada)
                entradas.append(df_archivo)
                nombres.append(archivo.name)
            except Exception as error_archivo:
                raise ValueError(f"Error en {archivo.name}: {error_archivo}") from error_archivo
        import pandas as pd
        df = pd.concat(entradas, ignore_index=True)
        st.caption(
            f"{len(archivos)} archivo(s) procesado(s); {len(df)} registros normalizados. "
            "Las bases originales no se envían al modelo."
        )
        raiz = __import__("pathlib").Path(__file__).resolve().parent
        system_prompt = leer_prompt(raiz / "prompts" / "system_prompt.md")
        user_template = leer_prompt(raiz / "prompts" / "user_prompt.md")
        fecha = datetime.now(timezone.utc).isoformat()
        datos = df.where(df.notna(), None).to_dict(orient="records")
        prompt = (
            user_template
            .replace("{corrida_id}", corrida_id)
            .replace("{fecha_ejecucion}", fecha)
            .replace("{nombre_archivo}", ", ".join(nombres))
            .replace("{datos_json}", json.dumps(datos, ensure_ascii=False, indent=2))
        )
        with st.spinner("Analizando y validando la evidencia..."):
            client = genai.Client(api_key=clave)
            response = client.models.generate_content(
                model=modelo,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_json_schema=RESPONSE_SCHEMA,
                    temperature=0.1,
                ),
            )
            resultado_generado = json.loads(response.text)
            infracciones = detectar_infracciones(resultado_generado, df)
            responses = [response]
            if infracciones:
                correccion = (
                    "Revisá el siguiente borrador JSON sin recalcular ni inventar valores. "
                    "Conservá toda la evidencia válida y corregí únicamente los incumplimientos indicados.\n\n"
                    "BORRADOR:\n"
                    + json.dumps(resultado_generado, ensure_ascii=False, indent=2)
                    + "\n\nCONTROLES INCUMPLIDOS:\n- "
                    + "\n- ".join(infracciones)
                    + "\nCorregí todas las infracciones y devolvé nuevamente el JSON completo."
                )
                response_corregida = client.models.generate_content(
                    model=modelo,
                    contents=correccion,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json",
                        response_json_schema=RESPONSE_SCHEMA,
                        temperature=0.0,
                    ),
                )
                resultado_generado = json.loads(response_corregida.text)
                responses.append(response_corregida)
                infracciones = detectar_infracciones(resultado_generado, df)
            st.session_state["controles_salida"] = infracciones
        st.session_state["resultado"] = resultado_generado
        st.session_state["tokens"] = [getattr(r, "usage_metadata", None) for r in responses]
        st.session_state["metricas_ejecucion"] = calcular_metricas_ejecucion(responses, modelo)
    except Exception as error:
        mensaje = str(error)
        if "429" in mensaje or "RESOURCE_EXHAUSTED" in mensaje:
            st.error(
                "Gemini alcanzó temporalmente el límite de uso. Esperá un minuto y volvé a ejecutar; "
                "la aplicación no conservará un resultado anterior como si fuera nuevo."
            )
        else:
            st.error(f"No se pudo completar la corrida: {error}")

resultado = st.session_state.get("resultado")
if not resultado:
    st.info("Cargá una o más fuentes y ejecutá el análisis para ver el dashboard.")
    st.stop()

hipotesis = resultado["resultado_hipotesis"]
c1, c2, c3 = st.columns(3)
c1.metric("Resultado de la hipótesis", hipotesis["estado"].replace("_", " ").title())
c2.metric("Confianza en la conclusión", hipotesis["nivel_confianza"].title())
c3.metric("Calidad de datos", resultado["calidad_datos"]["estado"].title())
st.write(hipotesis["justificacion"])

controles_salida = st.session_state.get("controles_salida", [])
if controles_salida:
    st.warning("La revisión automática dejó puntos pendientes para supervisión humana: " + " ".join(controles_salida))

tab1, tab2, tab3, tab4 = st.tabs(["Hallazgos", "Oportunidades", "Debilidades", "Amenazas"])
with tab1:
    mostrar_tarjetas(resultado["dashboard"]["hallazgos"], "#2563EB")
with tab2:
    mostrar_tarjetas(resultado["dashboard"]["oportunidades"], "#16A34A")
with tab3:
    mostrar_tarjetas(resultado["dashboard"]["debilidades"], "#D97706")
with tab4:
    mostrar_tarjetas(resultado["dashboard"]["amenazas"], "#DC2626")

st.subheader("Acciones priorizadas")
st.dataframe(resultado["hallazgos_priorizados"], use_container_width=True, hide_index=True)

with st.expander("Calidad, contradicciones y revisión humana"):
    st.write("Problemas detectados:", resultado["calidad_datos"]["problemas_detectados"])
    st.write("Datos faltantes:", resultado["calidad_datos"]["datos_faltantes_relevantes"])
    st.write("Contradicciones:", resultado["contradicciones_entre_fuentes"])
    st.write("Puntos a revisar:", resultado["revision_humana"]["puntos_a_revisar"])
    st.write("Responsable final:", resultado["revision_humana"]["responsable_final"])

metricas_ejecucion = st.session_state.get("metricas_ejecucion", {})
if metricas_ejecucion:
    with st.expander("Consumo y costo estimado de la corrida"):
        m1, m2, m3 = st.columns(3)
        m1.metric("Tokens de entrada", f"{metricas_ejecucion['tokens_entrada']:,}")
        m2.metric("Tokens de salida", f"{metricas_ejecucion['tokens_salida']:,}")
        m3.metric("Costo estimado", f"USD {metricas_ejecucion['costo_estimado_usd']:.6f}")
        st.caption(
            f"{metricas_ejecucion['llamadas_modelo']} llamada(s) a {metricas_ejecucion['modelo']}. "
            "Estimación a tarifa paga de referencia; el costo efectivo puede ser USD 0 en el nivel gratuito."
        )

resultado_descarga = dict(resultado)
if metricas_ejecucion:
    resultado_descarga["metricas_ejecucion"] = metricas_ejecucion

st.download_button(
    "Descargar salida JSON",
    data=json.dumps(resultado_descarga, ensure_ascii=False, indent=2),
    file_name=f"{resultado['corrida']['id']}_salida.json",
    mime="application/json",
)
