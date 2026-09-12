import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


COLUMNAS_OBLIGATORIAS = [
    "periodo",
    "temporalidad",
    "fuente",
    "area",
    "calibre_ml",
    "sabor",
    "volumen_cc",
    "clientes_con_compra",
    "stock_cc",
    "volumen_fytd_cc",
    "wd_pct",
    "nd_pct",
    "datos_anonimizados",
    "unidad_volumen",
    "base_indice",
]

FUENTES_VALIDAS = {"sell_in", "sell_out_distribuidores", "logyt", "scentia"}
TEMPORALIDADES_VALIDAS = {"LM", "FYTD", "L12M"}
SABORES_VALIDOS = {"VODKA", "LIMON", "GREEN_APPLE", "RED_BERRIES", "TOTAL_DRL"}
CALIBRES_VALIDOS = {473, 1000}


RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "corrida": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "fecha_ejecucion": {"type": "string"},
                "archivo": {"type": "string"},
                "fuentes_analizadas": {"type": "array", "items": {"type": "string"}},
                "periodos_analizados": {"type": "array", "items": {"type": "string"}},
                "temporalidades": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["id", "fecha_ejecucion", "archivo", "fuentes_analizadas", "periodos_analizados", "temporalidades"],
        },
        "calidad_datos": {
            "type": "object",
            "properties": {
                "estado": {"type": "string", "enum": ["suficiente", "parcial", "insuficiente"]},
                "problemas_detectados": {"type": "array", "items": {"type": "string"}},
                "datos_faltantes_relevantes": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["estado", "problemas_detectados", "datos_faltantes_relevantes"],
        },
        "resultado_hipotesis": {
            "type": "object",
            "properties": {
                "estado": {"type": "string", "enum": ["validada", "parcialmente_validada", "rechazada", "evidencia_insuficiente"]},
                "justificacion": {"type": "string"},
                "nivel_confianza": {"type": "string", "enum": ["alto", "medio", "bajo"]},
            },
            "required": ["estado", "justificacion", "nivel_confianza"],
        },
        "desempeno_por_calibre": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "calibre": {"type": "string"},
                    "evidencia": {"type": "array", "items": {"type": "string"}},
                    "interpretacion": {"type": "string"},
                    "limitaciones": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["calibre", "evidencia", "interpretacion", "limitaciones"],
            },
        },
        "rol_por_sabor": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "sabor": {"type": "string"},
                    "calibre": {"type": "string"},
                    "evidencia": {"type": "array", "items": {"type": "string"}},
                    "interpretacion": {"type": "string"},
                    "dato_faltante": {"type": "string"},
                },
                "required": ["sabor", "calibre", "evidencia", "interpretacion", "dato_faltante"],
            },
        },
        "hallazgos_priorizados": {
            "type": "array",
            "maxItems": 5,
            "items": {
                "type": "object",
                "properties": {
                    "prioridad": {"type": "integer"},
                    "nivel": {"type": "string", "enum": ["total_marca", "calibre", "sabor", "area"]},
                    "fuente": {"type": "string"},
                    "periodo": {"type": "string"},
                    "temporalidad": {"type": "string"},
                    "evidencia": {"type": "string"},
                    "interpretacion": {"type": "string"},
                    "accion_sugerida": {"type": "string"},
                    "responsable_sugerido": {"type": "string", "enum": ["Marketing", "Comercial", "Trade Marketing", "Supply"]},
                    "kpi_seguimiento": {"type": "string"},
                    "confianza": {"type": "string", "enum": ["alta", "media", "baja"]},
                },
                "required": ["prioridad", "nivel", "fuente", "periodo", "temporalidad", "evidencia", "interpretacion", "accion_sugerida", "responsable_sugerido", "kpi_seguimiento", "confianza"],
            },
        },
        "dashboard": {
            "type": "object",
            "properties": {
                categoria: {
                    "type": "array",
                    "maxItems": 3,
                    "items": {
                        "type": "object",
                        "properties": {
                            "titulo": {"type": "string"},
                            "evidencia": {"type": "string"},
                            "fuente": {"type": "string"},
                            "periodo": {"type": "string"},
                            "interpretacion": {"type": "string"},
                            "confianza": {"type": "string", "enum": ["alta", "media", "baja"]},
                        },
                        "required": ["titulo", "evidencia", "fuente", "periodo", "interpretacion", "confianza"],
                    },
                }
                for categoria in ["hallazgos", "oportunidades", "debilidades", "amenazas"]
            },
            "required": ["hallazgos", "oportunidades", "debilidades", "amenazas"],
        },
        "contradicciones_entre_fuentes": {"type": "array", "items": {"type": "string"}},
        "revision_humana": {
            "type": "object",
            "properties": {
                "requiere_revision_humana": {"type": "boolean"},
                "puntos_a_revisar": {"type": "array", "items": {"type": "string"}},
                "responsable_final": {"type": "string"},
            },
            "required": ["requiere_revision_humana", "puntos_a_revisar", "responsable_final"],
        },
    },
    "required": ["corrida", "calidad_datos", "resultado_hipotesis", "desempeno_por_calibre", "rol_por_sabor", "hallazgos_priorizados", "dashboard", "contradicciones_entre_fuentes", "revision_humana"],
}


def validar_y_preparar(ruta_csv: Path) -> tuple[pd.DataFrame, list[str]]:
    if isinstance(ruta_csv, pd.DataFrame):
        df = ruta_csv.copy()
    else:
        df = pd.read_csv(ruta_csv, dtype={"periodo": "string", "temporalidad": "string", "fuente": "string", "area": "string", "sabor": "string"})
    faltantes = [columna for columna in COLUMNAS_OBLIGATORIAS if columna not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas obligatorias: {', '.join(faltantes)}")
    if df.empty:
        raise ValueError("El archivo no contiene filas de datos.")

    df = df[COLUMNAS_OBLIGATORIAS].copy()
    for columna in [
        "calibre_ml",
        "volumen_cc",
        "clientes_con_compra",
        "stock_cc",
        "volumen_fytd_cc",
        "wd_pct",
        "nd_pct",
    ]:
        df[columna] = pd.to_numeric(df[columna], errors="coerce")

    errores = []
    fuentes_invalidas = sorted(set(df["fuente"].dropna()) - FUENTES_VALIDAS)
    temporalidades_invalidas = sorted(set(df["temporalidad"].dropna()) - TEMPORALIDADES_VALIDAS)
    sabores_invalidos = sorted(set(df["sabor"].dropna()) - SABORES_VALIDOS)
    calibres_invalidos = sorted(set(df["calibre_ml"].dropna().astype(int)) - CALIBRES_VALIDOS)
    if fuentes_invalidas:
        errores.append(f"Fuentes no reconocidas: {fuentes_invalidas}")
    if temporalidades_invalidas:
        errores.append(f"Temporalidades no reconocidas: {temporalidades_invalidas}")
    if sabores_invalidos:
        errores.append(f"Sabores no reconocidos: {sabores_invalidos}")
    if calibres_invalidos:
        errores.append(f"Calibres no reconocidos: {calibres_invalidos}")
    if df["volumen_cc"].isna().any():
        errores.append("Hay filas sin volumen_cc numérico.")
    unidades_invalidas = sorted(set(df["unidad_volumen"].dropna()) - {"CC", "INDICE"})
    if unidades_invalidas:
        errores.append(f"Unidades de volumen no reconocidas: {unidades_invalidas}")
    anonimizados = df["datos_anonimizados"].astype(str).str.lower().isin({"true", "1", "si", "sí"})
    if (anonimizados & (df["unidad_volumen"] != "INDICE")).any():
        errores.append("Las filas anonimizadas deben declarar unidad_volumen=INDICE.")
    if (anonimizados & df["base_indice"].isna()).any():
        errores.append("Las filas anonimizadas deben informar base_indice.")
    bases_por_grupo = (
        df.loc[anonimizados]
        .groupby(["fuente", "calibre_ml"], dropna=False)["base_indice"]
        .nunique(dropna=True)
    )
    if (bases_por_grupo > 1).any():
        errores.append("Hay bases de índice incompatibles dentro de una misma fuente y calibre.")
    if errores:
        raise ValueError(" ".join(errores))

    df["rotacion_proxy"] = None
    mascara_clientes = (
        df["fuente"].isin(["sell_in", "sell_out_distribuidores"])
        & df["clientes_con_compra"].notna()
        & (df["clientes_con_compra"] > 0)
    )
    df.loc[mascara_clientes, "rotacion_proxy"] = (
        df.loc[mascara_clientes, "volumen_cc"] / df.loc[mascara_clientes, "clientes_con_compra"]
    ).round(3)
    mascara_scentia = (
        (df["fuente"] == "scentia")
        & df["nd_pct"].notna()
        & (df["nd_pct"] > 0)
    )
    df.loc[mascara_scentia, "rotacion_proxy"] = (
        df.loc[mascara_scentia, "volumen_cc"] / df.loc[mascara_scentia, "nd_pct"]
    ).round(3)

    df["relacion_stock_sellout"] = None
    mascara_stock = (df["fuente"] == "logyt") & df["stock_cc"].notna() & (df["volumen_cc"] > 0)
    df.loc[mascara_stock, "relacion_stock_sellout"] = (
        df.loc[mascara_stock, "stock_cc"] / df.loc[mascara_stock, "volumen_cc"]
    ).round(3)

    claves_mix = ["periodo", "temporalidad", "fuente", "area", "calibre_ml"]
    totales = (
        df[df["sabor"] == "TOTAL_DRL"][claves_mix + ["volumen_cc"]]
        .rename(columns={"volumen_cc": "volumen_total_calibre_cc"})
    )
    df = df.merge(totales, on=claves_mix, how="left")
    df["mix_sabor"] = None
    mascara_mix = (df["sabor"] != "TOTAL_DRL") & (df["volumen_total_calibre_cc"] > 0)
    df.loc[mascara_mix, "mix_sabor"] = (
        df.loc[mascara_mix, "volumen_cc"] / df.loc[mascara_mix, "volumen_total_calibre_cc"]
    ).round(4)
    return df, []


def leer_prompt(ruta: Path) -> str:
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró el prompt: {ruta}")
    return ruta.read_text(encoding="utf-8")


def main() -> None:
    from google import genai
    from google.genai import types

    parser = argparse.ArgumentParser(description="Ejecuta el DRL Core Portfolio Agent.")
    parser.add_argument("entrada", type=Path, help="Ruta al CSV normalizado")
    parser.add_argument("--corrida", required=True, help="Identificador, por ejemplo corrida_01")
    parser.add_argument("--salida", type=Path, default=Path("salida"), help="Carpeta de salida")
    parser.add_argument("--modelo", default="gemini-3.5-flash-lite", help="Modelo Gemini")
    args = parser.parse_args()

    if not os.getenv("GEMINI_API_KEY"):
        raise EnvironmentError("Falta la variable GEMINI_API_KEY. No guardes la clave en el repositorio.")

    raiz = Path(__file__).resolve().parent
    system_prompt = leer_prompt(raiz / "prompts" / "system_prompt.md")
    user_template = leer_prompt(raiz / "prompts" / "user_prompt.md")
    df, _ = validar_y_preparar(args.entrada)

    fecha = datetime.now(timezone.utc).isoformat()
    datos_json = df.where(pd.notna(df), None).to_dict(orient="records")
    user_prompt = (
        user_template
        .replace("{corrida_id}", args.corrida)
        .replace("{fecha_ejecucion}", fecha)
        .replace("{nombre_archivo}", args.entrada.name)
        .replace("{datos_json}", json.dumps(datos_json, ensure_ascii=False, indent=2))
    )

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model=args.modelo,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_json_schema=RESPONSE_SCHEMA,
            temperature=0.1,
        ),
    )
    resultado = json.loads(response.text)

    args.salida.mkdir(parents=True, exist_ok=True)
    (args.salida / "salida.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (args.salida / "datos_procesados.json").write_text(
        json.dumps(datos_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    usage = getattr(response, "usage_metadata", None)
    metadatos = {
        "corrida_id": args.corrida,
        "fecha_ejecucion_utc": fecha,
        "archivo_entrada": args.entrada.name,
        "modelo": args.modelo,
        "tokens_prompt": getattr(usage, "prompt_token_count", None) if usage else None,
        "tokens_salida": getattr(usage, "candidates_token_count", None) if usage else None,
        "tokens_totales": getattr(usage, "total_token_count", None) if usage else None,
    }
    (args.salida / "metadatos.json").write_text(
        json.dumps(metadatos, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Corrida completada. Resultado: {args.salida / 'salida.json'}")


if __name__ == "__main__":
    main()
