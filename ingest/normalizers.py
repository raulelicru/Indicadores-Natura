"""Normalización de DataFrames crudos al esquema canónico del proyecto.

Cada helper (``_build_rem_cols``, ``_build_pag_cols``, ``_build_gest_cols``,
``_build_prom_cols``) normaliza los nombres de columna a minúsculas y prueba
una lista de aliases en orden de prioridad, aceptando el primero que exista.
"""
from __future__ import annotations

import re
import unicodedata

import numpy as np
import pandas as pd

from logic.temporalidad import pac_temporalidad


def _slug(texto: str) -> str:
    """Normaliza un nombre de columna: minúsculas, sin acentos, con _."""
    t = str(texto).strip().lower()
    t = "".join(
        c for c in unicodedata.normalize("NFKD", t)
        if not unicodedata.combining(c)
    )
    t = re.sub(r"[^a-z0-9]+", "_", t)
    return t.strip("_")


def _mapa_slug(df: pd.DataFrame) -> dict[str, str]:
    """Mapa slug -> nombre real de columna."""
    return {_slug(c): c for c in df.columns}


def _primero(df: pd.DataFrame, mapa: dict[str, str], aliases: list[str]):
    """Devuelve la serie de la primera columna cuyo slug coincide con un alias."""
    for alias in aliases:
        s = _slug(alias)
        if s in mapa:
            return df[mapa[s]]
    return None


def _num(serie):
    if serie is None:
        return None
    return pd.to_numeric(
        serie.astype(str).str.replace(r"[^0-9,.\-]", "", regex=True)
        .str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
        errors="coerce",
    )


def _num_simple(serie):
    if serie is None:
        return None
    return pd.to_numeric(serie, errors="coerce")


def _texto(serie):
    if serie is None:
        return None
    return serie.astype(str).str.strip()


def _fecha(serie):
    if serie is None:
        return None
    return pd.to_datetime(serie, errors="coerce", dayfirst=True)


# ---------------------------------------------------------------------------
# CARTERA / REMESA
# ---------------------------------------------------------------------------
def _build_rem_cols(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=[
            "codigo_de_cliente", "aging_de_morosidad", "valor_saldo_deuda",
            "segmentacion_rep", "rango_edad_consultora", "zona", "estado",
            "temporalidad",
        ])
    m = _mapa_slug(df)
    out = pd.DataFrame()
    out["codigo_de_cliente"] = _texto(_primero(df, m, [
        "codigo_de_cliente", "codigo_cliente", "cod_cliente", "codigo",
        "cliente", "id_cliente",
    ]))
    aging = _num_simple(_primero(df, m, [
        "aging_de_morosidad", "aging", "aging_morosidad", "dias_mora",
        "dias_de_mora", "morosidad",
    ]))
    out["aging_de_morosidad"] = aging
    out["valor_saldo_deuda"] = _num_simple(_primero(df, m, [
        "valor_saldo_deuda", "saldo_deuda", "saldo", "valor_deuda", "deuda",
        "valor_saldo", "monto_deuda",
    ]))
    out["segmentacion_rep"] = _texto(_primero(df, m, [
        "segmentacion_rep", "segmentacion", "segmento", "segmento_rep",
    ]))
    out["rango_edad_consultora"] = _texto(_primero(df, m, [
        "rango_del_edad_consultora", "rango_edad_consultora",
        "rango_edad", "camino_crecimiento", "camino_de_crecimiento",
    ]))
    out["zona"] = _texto(_primero(df, m, ["zona", "region", "territorio"]))
    out["estado"] = _texto(_primero(df, m, [
        "estado", "status", "estatus", "situacion",
    ]))
    out["temporalidad"] = out["aging_de_morosidad"].apply(pac_temporalidad)
    return out


# ---------------------------------------------------------------------------
# PAGOS
# ---------------------------------------------------------------------------
def _build_pag_cols(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=[
            "codigo_de_cliente", "pago", "fecha_pago", "asesor", "temporalidad",
        ])
    m = _mapa_slug(df)
    out = pd.DataFrame()
    out["codigo_de_cliente"] = _texto(_primero(df, m, [
        "codigo_de_cliente", "codigo_cliente", "cod_cliente", "codigo", "cliente",
    ]))
    out["pago"] = _num_simple(_primero(df, m, [
        "pago", "valor_pago", "monto_pago", "monto", "importe", "valor",
    ]))
    out["fecha_pago"] = _fecha(_primero(df, m, [
        "fecha_pago", "fecha", "fecha_de_pago", "data_pagamento",
    ]))
    out["asesor"] = _texto(_primero(df, m, [
        "asesor", "agente", "gestor", "ejecutivo", "operador",
    ]))
    aging = _num_simple(_primero(df, m, [
        "aging_de_morosidad", "aging", "dias_mora",
    ]))
    temp = _texto(_primero(df, m, ["temporalidad", "temp"]))
    if temp is not None:
        out["temporalidad"] = temp
    elif aging is not None:
        out["temporalidad"] = aging.apply(pac_temporalidad)
    else:
        out["temporalidad"] = np.nan
    return out


# ---------------------------------------------------------------------------
# GESTION (Vici)
# ---------------------------------------------------------------------------
def _build_gest_cols(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=[
            "codigo_de_cliente", "list_description", "contactabilidad",
            "hora_llamada", "canal", "asesor", "duracion_seg",
        ])
    m = _mapa_slug(df)
    out = pd.DataFrame()
    out["codigo_de_cliente"] = _texto(_primero(df, m, [
        "codigo_de_cliente", "codigo_cliente", "cod_cliente", "codigo",
        "cliente", "phone_code", "vendor_lead_code",
    ]))
    out["list_description"] = _texto(_primero(df, m, [
        "list_description", "list_name", "descripcion_lista", "disposicion",
        "status", "estatus_llamada",
    ]))
    out["contactabilidad"] = _texto(_primero(df, m, [
        "contactabilidad", "contacto", "contactable", "tipo_contacto",
    ]))
    out["hora_llamada"] = _texto(_primero(df, m, [
        "hora_llamada", "hora", "call_time", "hora_de_llamada",
    ]))
    out["canal"] = _texto(_primero(df, m, [
        "canal", "channel", "medio", "tipo_canal",
    ]))
    out["asesor"] = _texto(_primero(df, m, [
        "asesor", "agente", "user", "usuario", "operador", "gestor",
    ]))
    out["duracion_seg"] = _num_simple(_primero(df, m, [
        "duracion_seg", "duracion", "length_in_sec", "duration", "segundos",
    ]))
    return out


# ---------------------------------------------------------------------------
# PROMESAS
# ---------------------------------------------------------------------------
def _build_prom_cols(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=[
            "codigo_de_cliente", "monto_promesa", "fecha_promesa", "estatus",
        ])
    m = _mapa_slug(df)
    out = pd.DataFrame()
    out["codigo_de_cliente"] = _texto(_primero(df, m, [
        "codigo_de_cliente", "codigo_cliente", "cod_cliente", "codigo", "cliente",
    ]))
    out["monto_promesa"] = _num_simple(_primero(df, m, [
        "monto_promesa", "monto", "valor_promesa", "importe_promesa",
        "valor", "importe",
    ]))
    out["fecha_promesa"] = _fecha(_primero(df, m, [
        "fecha_promesa", "fecha", "fecha_de_promesa", "fecha_compromiso",
    ]))
    out["estatus"] = _texto(_primero(df, m, [
        "estatus", "estado", "cumplida", "status", "situacion",
    ]))
    return out


# Registro de normalizadores por tipo de archivo.
NORMALIZADORES = {
    "cartera": _build_rem_cols,
    "pagos": _build_pag_cols,
    "gestion": _build_gest_cols,
    "promesas": _build_prom_cols,
}


def normalizar(tipo_archivo: str, df: pd.DataFrame) -> pd.DataFrame:
    """Aplica el normalizador correspondiente al tipo de archivo."""
    fn = NORMALIZADORES.get(tipo_archivo)
    if fn is None:
        return df
    return fn(df)
