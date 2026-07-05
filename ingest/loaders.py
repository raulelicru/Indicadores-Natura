"""Lectura de archivos cargados (xlsx/xls/csv) cacheada sobre bytes."""
from __future__ import annotations

import io

import pandas as pd
import streamlit as st


def _leer_csv_bytes(data: bytes) -> pd.DataFrame:
    ultimo_error: Exception | None = None
    for encoding in ("utf-8-sig", "latin-1"):
        for sep in (",", ";", "\t", "|"):
            try:
                df = pd.read_csv(io.BytesIO(data), encoding=encoding, sep=sep)
                if df.shape[1] > 1:
                    return df
            except Exception as exc:  # noqa: BLE001
                ultimo_error = exc
    # Último intento: separador por defecto, utf-8-sig.
    try:
        return pd.read_csv(io.BytesIO(data), encoding="utf-8-sig")
    except Exception as exc:  # noqa: BLE001
        raise ultimo_error or exc


@st.cache_data(show_spinner=False)
def leer_tabla(data: bytes, nombre_archivo: str, hoja: str | int | None = 0) -> pd.DataFrame:
    """Lee bytes de un archivo a DataFrame según su extensión.

    Cacheado sobre ``data`` (bytes) para evitar re-lecturas al re-renderizar.
    """
    nombre = (nombre_archivo or "").lower()
    if nombre.endswith(".csv") or nombre.endswith(".txt"):
        return _leer_csv_bytes(data)
    if nombre.endswith(".xls"):
        return pd.read_excel(io.BytesIO(data), sheet_name=hoja, engine="xlrd")
    # Por defecto xlsx.
    return pd.read_excel(io.BytesIO(data), sheet_name=hoja, engine="openpyxl")


@st.cache_data(show_spinner=False)
def listar_hojas(data: bytes, nombre_archivo: str) -> list[str]:
    """Lista de hojas de un Excel; vacío para CSV."""
    nombre = (nombre_archivo or "").lower()
    if nombre.endswith(".csv") or nombre.endswith(".txt"):
        return []
    engine = "xlrd" if nombre.endswith(".xls") else "openpyxl"
    try:
        xls = pd.ExcelFile(io.BytesIO(data), engine=engine)
        return list(xls.sheet_names)
    except Exception:  # noqa: BLE001
        return []
