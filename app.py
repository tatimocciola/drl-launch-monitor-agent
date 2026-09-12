import json
import os
from datetime import datetime, timezone

import streamlit as st
from google import genai
from google.genai import types

from ejecutar_agente import RESPONSE_SCHEMA, leer_prompt, validar_y_preparar


st.set_page_config(page_title="DRL Core Portfolio Agent", page_icon="📊", layout="wide")


def mostrar_tarjetas(elementos, color):
    if not elementos:
        st.info("No se identificaron elementos con evidencia suficiente.")
        return
    for item in elementos:
        st.markdown(
            f"""
            <div style="border-left: 5px solid {color}; padding: 12px 16px; margin: 10px 0;
                        background: #ffffff; border-radius: 6px; box-shadow: 0 1px 4px #00000018;">
              <strong>{item.get('titulo', 'Sin título')}</strong><br>
              <small>{item.get('fuente', '')} · {item.get('periodo', '')}</small><br>
              <b>Evidencia:</b> {item.get('evidencia', '')}<br>
              <b>Interpretación:</b> {item.get('interpretacion', '')}<br>
              <b>Confianza:</b> {item.get('confianza', '')}
            </div>
            """,
            unsafe_allow_html=True,
        )


st.title("DRL Core Portfolio Agent")
st.caption("Evaluación supervisada del rol de Vodka, Limón, Green Apple y Red Berries en 473 ml y 1 L")

with st.sidebar:
    st.header("Nueva corrida")
    archivo = st.file_uploader("Archivo CSV normalizado", type=["csv"])
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
    if archivo is None:
        st.error("Seleccioná un archivo CSV.")
        st.stop()
    if not clave:
        st.error("Ingresá la Gemini API key. La aplicación no la guarda.")
        st.stop()

    try:
        df, _ = validar_y_preparar(archivo)
        raiz = __import__("pathlib").Path(__file__).resolve().parent
        system_prompt = leer_prompt(raiz / "prompts" / "system_prompt.md")
        user_template = leer_prompt(raiz / "prompts" / "user_prompt.md")
        fecha = datetime.now(timezone.utc).isoformat()
        datos = df.where(df.notna(), None).to_dict(orient="records")
        prompt = (
            user_template
            .replace("{corrida_id}", corrida_id)
            .replace("{fecha_ejecucion}", fecha)
            .replace("{nombre_archivo}", archivo.name)
            .replace("{datos_json}", json.dumps(datos, ensure_ascii=False, indent=2))
        )
        with st.spinner("Analizando la evidencia..."):
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
        st.session_state["resultado"] = json.loads(response.text)
        st.session_state["tokens"] = getattr(response, "usage_metadata", None)
    except Exception as error:
        st.error(f"No se pudo completar la corrida: {error}")

resultado = st.session_state.get("resultado")
if not resultado:
    st.info("Cargá un CSV y ejecutá el análisis para ver el dashboard.")
    st.stop()

hipotesis = resultado["resultado_hipotesis"]
c1, c2, c3 = st.columns(3)
c1.metric("Resultado de la hipótesis", hipotesis["estado"].replace("_", " ").title())
c2.metric("Confianza", hipotesis["nivel_confianza"].title())
c3.metric("Calidad de datos", resultado["calidad_datos"]["estado"].title())
st.write(hipotesis["justificacion"])

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

st.download_button(
    "Descargar salida JSON",
    data=json.dumps(resultado, ensure_ascii=False, indent=2),
    file_name=f"{resultado['corrida']['id']}_salida.json",
    mime="application/json",
)
