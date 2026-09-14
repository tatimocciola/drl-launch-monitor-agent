import argparse
import hashlib
import json
import os
import re
import platform
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


def validar_y_preparar(ruta_csv: Path) -> tuple[pd.DataFrame, dict]:
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
    advertencias = []
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
    periodos_invalidos = sorted({
        str(periodo) for periodo in df["periodo"].dropna()
        if not re.fullmatch(r"\d{6}", str(periodo)) or not 1 <= int(str(periodo)[4:6]) <= 12
    })
    if periodos_invalidos:
        errores.append(f"Períodos inválidos; se espera AAAAMM: {periodos_invalidos[:10]}")
    for columna in ["volumen_cc", "clientes_con_compra", "stock_cc", "volumen_fytd_cc"]:
        cantidad = int((df[columna].dropna() < 0).sum())
        if cantidad:
            errores.append(f"{columna} contiene {cantidad} valor(es) negativo(s).")
    for columna in ["wd_pct", "nd_pct"]:
        cantidad = int(((df[columna].dropna() < 0) | (df[columna].dropna() > 100)).sum())
        if cantidad:
            errores.append(f"{columna} contiene {cantidad} valor(es) fuera del rango 0-100.")
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

    claves_registro = ["periodo", "temporalidad", "fuente", "area", "calibre_ml", "sabor"]
    duplicados = int(df.duplicated(claves_registro, keep=False).sum())
    if duplicados:
        advertencias.append(
            f"Se detectaron {duplicados} filas con claves repetidas; deben revisarse antes de sumar volúmenes."
        )
    if (df["fuente"].eq("scentia") & df["nd_pct"].isna()).any():
        advertencias.append("Hay filas Scentia sin ND; no se calculará rotación para esas observaciones.")
    if (df["fuente"].eq("logyt") & df["stock_cc"].isna()).any():
        advertencias.append("Hay filas Logyt sin stock; no se evaluará cobertura para esas observaciones.")

    # Controles cruzados: detectan incompatibilidades antes de enviar datos al modelo.
    fuentes_por_unidad = (
        df.groupby("fuente", dropna=False)["unidad_volumen"]
        .apply(lambda valores: sorted(set(valores.dropna().astype(str))))
        .to_dict()
    )
    for fuente, unidades in fuentes_por_unidad.items():
        if len(unidades) > 1:
            errores.append(f"La fuente {fuente} mezcla unidades incompatibles: {unidades}.")

    claves_cruce = ["periodo", "temporalidad", "area", "calibre_ml", "sabor"]
    unidades_por_clave = df.groupby(claves_cruce, dropna=False)["unidad_volumen"].nunique(dropna=True)
    cruces_unidades_incompatibles = int((unidades_por_clave > 1).sum())
    if cruces_unidades_incompatibles:
        advertencias.append(
            f"Hay {cruces_unidades_incompatibles} clave(s) coincidentes entre fuentes con unidades distintas; "
            "se permite contrastar dirección y cobertura, pero no sumar ni comparar magnitudes."
        )

    periodos_por_fuente = {
        fuente: set(grupo["periodo"].dropna().astype(str))
        for fuente, grupo in df.groupby("fuente")
    }
    pares_sin_solapamiento = []
    fuentes_lista = sorted(periodos_por_fuente)
    for indice, fuente_a in enumerate(fuentes_lista):
        for fuente_b in fuentes_lista[indice + 1:]:
            if not periodos_por_fuente[fuente_a].intersection(periodos_por_fuente[fuente_b]):
                pares_sin_solapamiento.append(f"{fuente_a}/{fuente_b}")
    if pares_sin_solapamiento:
        advertencias.append(
            "Fuentes sin períodos coincidentes: " + ", ".join(pares_sin_solapamiento)
            + ". No deben cruzarse como si correspondieran al mismo corte."
        )
    if errores:
        raise ValueError(" ".join(errores))

    reporte_integridad = {
        "estado": "aprobado_con_advertencias" if advertencias else "aprobado",
        "controles_ejecutados": [
            "columnas obligatorias", "archivo no vacío", "dominios admitidos",
            "período AAAAMM", "valores no negativos", "porcentajes entre 0 y 100",
            "unidad y anonimización coherentes", "base de índice compatible",
            "claves duplicadas", "campos necesarios para métricas por fuente",
            "unidades compatibles dentro de cada fuente", "unidades compatibles entre fuentes",
            "solapamiento de períodos entre fuentes",
        ],
        "errores": [],
        "advertencias": advertencias,
        "filas": int(len(df)),
        "fuentes": sorted(df["fuente"].dropna().astype(str).unique().tolist()),
        "periodo_minimo": str(df["periodo"].dropna().min()),
        "periodo_maximo": str(df["periodo"].dropna().max()),
        "filas_duplicadas_por_clave": duplicados,
        "claves_con_unidades_incompatibles": cruces_unidades_incompatibles,
        "pares_fuentes_sin_periodo_comun": pares_sin_solapamiento,
        "unidades_por_fuente": fuentes_por_unidad,
    }

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
    return df, reporte_integridad


def construir_log_consumo(response, corrida_id: str, fecha: str, modelo: str) -> dict:
    usage = getattr(response, "usage_metadata", None)
    tokens_entrada = int(getattr(usage, "prompt_token_count", 0) or 0) if usage else 0
    tokens_salida = int(getattr(usage, "candidates_token_count", 0) or 0) if usage else 0
    tokens_totales = int(getattr(usage, "total_token_count", 0) or 0) if usage else 0
    tarifa_entrada = 0.30
    tarifa_salida = 2.50
    costo = tokens_entrada / 1_000_000 * tarifa_entrada + tokens_salida / 1_000_000 * tarifa_salida
    return {
        "corrida_id": corrida_id,
        "fecha_ejecucion_utc": fecha,
        "modelo": modelo,
        "tokens_entrada": tokens_entrada,
        "tokens_salida": tokens_salida,
        "tokens_totales": tokens_totales,
        "tarifa_entrada_usd_por_millon": tarifa_entrada,
        "tarifa_salida_usd_por_millon": tarifa_salida,
        "costo_estimado_usd": round(costo, 6),
        "fuente_medicion": "usage_metadata devuelto por Gemini API",
        "tarifa_referencia": "https://ai.google.dev/gemini-api/docs/pricing",
        "tarifa_referencia_fecha": "2026-09-13",
    }


def generar_reporte_ejecucion(resultado: dict, integridad: dict, consumo: dict) -> str:
    corrida = resultado.get("corrida", {})
    hipotesis = resultado.get("resultado_hipotesis", {})
    revision = resultado.get("revision_humana", {})
    advertencias = integridad.get("advertencias", [])
    hallazgos = resultado.get("hallazgos_priorizados", [])
    lineas_hallazgos = [
        f"{h.get('prioridad', '-')}. {h.get('evidencia', '')} — Acción propuesta: {h.get('accion_sugerida', '')}"
        for h in hallazgos
    ] or ["- No se generaron hallazgos priorizados."]
    return "\n".join([
        f"# Reporte final de ejecución — {corrida.get('id', consumo.get('corrida_id', 'sin_id'))}",
        "", f"- Fecha UTC: {corrida.get('fecha_ejecucion', consumo.get('fecha_ejecucion_utc', ''))}",
        f"- Archivos: {corrida.get('archivo', '')}",
        f"- Fuentes: {', '.join(corrida.get('fuentes_analizadas', []))}",
        f"- Períodos: {', '.join(corrida.get('periodos_analizados', []))}",
        "", "## Integridad de datos", "",
        f"Estado: **{integridad.get('estado', 'sin_dato')}**. Filas procesadas: {integridad.get('filas', 0)}.",
        *( ["", "Advertencias:", *[f"- {a}" for a in advertencias]] if advertencias else ["", "Sin advertencias de integridad."] ),
        "", "## Resultado de la hipótesis", "",
        f"Estado: **{hipotesis.get('estado', '')}**. Confianza: **{hipotesis.get('nivel_confianza', '')}**.",
        "", hipotesis.get("justificacion", ""), "", "## Hallazgos y acciones", "", *lineas_hallazgos,
        "", "## Consumo de API", "",
        f"- Modelo: {consumo.get('modelo', '')}",
        f"- Tokens de entrada: {consumo.get('tokens_entrada', 0)}",
        f"- Tokens de salida: {consumo.get('tokens_salida', 0)}",
        f"- Tokens totales: {consumo.get('tokens_totales', 0)}",
        f"- Costo estimado a tarifa paga: USD {consumo.get('costo_estimado_usd', 0):.6f}",
        "", "## Supervisión", "",
        f"Requiere revisión humana: {revision.get('requiere_revision_humana', True)}.",
        f"Responsable final: {revision.get('responsable_final', 'Brand Manager')}.",
        "Las recomendaciones no se ejecutan hasta recibir aprobación humana o aplicar el plan de contingencia documentado.",
    ])


def sha256_archivo(ruta: Path) -> str:
    digest = hashlib.sha256()
    with ruta.open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            digest.update(bloque)
    return digest.hexdigest()


def generar_reporte_reproducibilidad(
    archivos: list[dict], integridad: dict, modelo: str, system_prompt: str, user_template: str
) -> dict:
    return {
        "estado": "reproducible" if not integridad.get("errores") else "no_reproducible",
        "fecha_generacion_utc": datetime.now(timezone.utc).isoformat(),
        "archivos_entrada": archivos,
        "integridad": integridad,
        "entorno": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "modelo": modelo,
        },
        "prompts": {
            "system_prompt_sha256": hashlib.sha256(system_prompt.encode("utf-8")).hexdigest(),
            "user_prompt_sha256": hashlib.sha256(user_template.encode("utf-8")).hexdigest(),
        },
        "instruccion_reproduccion": (
            "Instalar requirements.txt y ejecutar ejecutar_agente.py con la misma entrada, modelo y prompts. "
            "Los hashes permiten verificar que los artefactos no cambiaron."
        ),
    }


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
    df, reporte_integridad = validar_y_preparar(args.entrada)
    reporte_reproducibilidad = generar_reporte_reproducibilidad(
        [{
            "nombre": args.entrada.name,
            "bytes": args.entrada.stat().st_size,
            "sha256": sha256_archivo(args.entrada),
        }],
        reporte_integridad,
        args.modelo,
        system_prompt,
        user_template,
    )

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

    consumo = construir_log_consumo(response, args.corrida, fecha, args.modelo)
    consumo["archivo_entrada"] = args.entrada.name
    (args.salida / "integridad_datos.json").write_text(
        json.dumps(reporte_integridad, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (args.salida / "reporte_reproducibilidad.json").write_text(
        json.dumps(reporte_reproducibilidad, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (args.salida / "log_consumo_api.json").write_text(
        json.dumps(consumo, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (args.salida / "reporte_ejecucion.md").write_text(
        generar_reporte_ejecucion(resultado, reporte_integridad, consumo), encoding="utf-8"
    )
    print(f"Corrida completada. Reporte: {args.salida / 'reporte_ejecucion.md'}")


if __name__ == "__main__":
    main()
