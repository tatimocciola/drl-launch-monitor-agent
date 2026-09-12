from io import BytesIO
from pathlib import PurePosixPath
from zipfile import BadZipFile, ZipFile

import pandas as pd


MAX_ARCHIVOS = 10
MAX_DESCOMPRIMIDO = 500 * 1024 * 1024
COLUMNAS = [
    "PERIODO", "TOTALBRAND", "Brand", "Calibre", "Volumen", "Ytd_Vol",
    "BANDERA", "AREA", "WD", "ND",
]
MAPA_SABORES = {
    "DR LEMON VODKA": "VODKA",
    "DR LEMON": "LIMON",
    "DR LEMON GREEN APPLE": "GREEN_APPLE",
    "DR LEMON RED BERRY": "RED_BERRIES",
}
COLUMNAS_SALIDA = [
    "periodo", "temporalidad", "fuente", "area", "calibre_ml", "sabor",
    "volumen_cc", "clientes_con_compra", "stock_cc", "volumen_fytd_cc",
    "wd_pct", "nd_pct", "datos_anonimizados", "unidad_volumen", "base_indice"
]


def extraer_xlsx_seguro(datos_zip: bytes) -> bytes:
    try:
        with ZipFile(BytesIO(datos_zip)) as archivo:
            miembros = [m for m in archivo.infolist() if not m.is_dir()]
            if len(miembros) > MAX_ARCHIVOS:
                raise ValueError(f"El ZIP contiene más de {MAX_ARCHIVOS} archivos.")
            if sum(m.file_size for m in miembros) > MAX_DESCOMPRIMIDO:
                raise ValueError("El contenido descomprimido supera 500 MB.")
            for miembro in miembros:
                ruta = PurePosixPath(miembro.filename.replace("\\", "/"))
                if ruta.is_absolute() or ".." in ruta.parts:
                    raise ValueError("El ZIP contiene una ruta no segura.")
            excels = [m for m in miembros if m.filename.lower().endswith(".xlsx")]
            if len(excels) != 1:
                raise ValueError("El ZIP debe contener un único archivo .xlsx de Scentia.")
            return archivo.read(excels[0])
    except BadZipFile as error:
        raise ValueError("El archivo no es un ZIP válido.") from error


def normalizar_scentia_zip(datos_zip: bytes) -> pd.DataFrame:
    excel_bytes = extraer_xlsx_seguro(datos_zip)
    libro = pd.ExcelFile(BytesIO(excel_bytes))
    registros = []

    for hoja in libro.sheet_names:
        df = pd.read_excel(libro, sheet_name=hoja, usecols=lambda c: c in COLUMNAS)
        faltantes = sorted(set(COLUMNAS) - set(df.columns))
        if faltantes:
            raise ValueError(f"La hoja {hoja} no tiene las columnas Scentia requeridas: {faltantes}")
        df = df[df["TOTALBRAND"] == "TOTAL DR LEMON"].copy()
        df["Calibre"] = pd.to_numeric(df["Calibre"], errors="coerce")
        df = df[df["Calibre"].isin([473, 1000])]
        if df.empty:
            continue
        periodo = pd.to_datetime(df["PERIODO"], errors="coerce").dropna()
        if periodo.empty:
            raise ValueError(f"No se pudo identificar el período de la hoja {hoja}.")
        periodo_txt = periodo.iloc[0].strftime("%Y%m")

        for calibre, grupo in df.groupby("Calibre"):
            volumen_total = grupo["Volumen"].sum(min_count=1)
            ytd_total = grupo["Ytd_Vol"].sum(min_count=1)
            if pd.notna(volumen_total):
                registros.append([periodo_txt, "LM", "scentia", "TOTAL", int(calibre), "TOTAL_DRL", volumen_total, None, None, ytd_total, None, None])

            core = grupo[grupo["Brand"].isin(MAPA_SABORES)].copy()
            for (brand, area), datos_sabor in core.groupby(["Brand", "AREA"], dropna=False):
                volumen = datos_sabor["Volumen"].sum(min_count=1)
                ytd = datos_sabor["Ytd_Vol"].sum(min_count=1)
                # ND y WD son porcentajes definidos por celda Scentia. Para evitar
                # inventar una distribución nacional, se conservan al nivel de área.
                nd = datos_sabor["ND"].sum(min_count=1)
                wd = datos_sabor["WD"].sum(min_count=1)
                if pd.notna(volumen):
                    registros.append([
                        periodo_txt, "LM", "scentia", str(area), int(calibre),
                        MAPA_SABORES[brand], volumen, None, None, ytd, wd, nd,
                    ])

    if not registros:
        raise ValueError("No se encontraron registros DR LEMON de 473 ml o 1 L.")

    salida = pd.DataFrame(registros, columns=COLUMNAS_SALIDA[:12])
    salida = salida.sort_values(["periodo", "calibre_ml", "sabor"]).reset_index(drop=True)
    primer_periodo = salida["periodo"].min()
    for calibre in [473, 1000]:
        mascara_base = (
            (salida["periodo"] == primer_periodo)
            & (salida["calibre_ml"] == calibre)
            & (salida["sabor"] == "TOTAL_DRL")
        )
        if not mascara_base.any():
            raise ValueError(f"Falta el total DR LEMON base para {calibre} ml.")
        base = salida.loc[mascara_base, "volumen_cc"].iloc[0]
        mascara = salida["calibre_ml"] == calibre
        salida.loc[mascara, "volumen_cc"] = (salida.loc[mascara, "volumen_cc"] * 100 / base).round(3)
        salida.loc[mascara, "volumen_fytd_cc"] = (salida.loc[mascara, "volumen_fytd_cc"] * 100 / base).round(3)

    salida["datos_anonimizados"] = True
    salida["unidad_volumen"] = "INDICE"
    salida["base_indice"] = salida["calibre_ml"].map(
        lambda calibre: f"Total DRL {calibre} ml {primer_periodo} = 100"
    )
    return salida[COLUMNAS_SALIDA]
