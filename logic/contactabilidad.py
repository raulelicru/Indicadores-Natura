"""Lógica de contactabilidad de la gestión telefónica (Vici)."""
from __future__ import annotations

import numpy as np
import pandas as pd

# Palabras clave que denotan contacto efectivo cuando no hay columna
# 'Contactabilidad' explícita (se infiere de list_description / disposición).
PALABRAS_CONTACTO = [
    "contacto", "contactado", "efectivo", "promesa", "acuerdo",
    "titular", "positivo", "hablo", "habló", "atiende", "atendio", "atendió",
    "pago", "compromiso",
]
PALABRAS_NO_CONTACTO = [
    "no contesta", "no contacto", "buzon", "buzón", "ocupado", "apagado",
    "equivocado", "fuera de servicio", "no existe", "colgo", "colgó",
    "sin respuesta", "no localizado", "ilocalizable",
]


def _clasifica_texto(texto: str) -> str:
    t = str(texto).strip().lower()
    if not t:
        return "No contacto"
    for palabra in PALABRAS_NO_CONTACTO:
        if palabra in t:
            return "No contacto"
    for palabra in PALABRAS_CONTACTO:
        if palabra in t:
            return "Contacto"
    return "No contacto"


def clasifica_contacto(valor_contactabilidad=None, list_description=None) -> str:
    """Devuelve 'Contacto' o 'No contacto'.

    Usa la columna ``Contactabilidad`` (AO) si trae información; si no, infiere
    a partir de ``list_description``.
    """
    if valor_contactabilidad is not None and str(valor_contactabilidad).strip():
        t = str(valor_contactabilidad).strip().lower()
        if any(p in t for p in PALABRAS_NO_CONTACTO):
            return "No contacto"
        if t in {"contacto", "si", "sí", "1", "true", "efectivo"} or \
                any(p in t for p in PALABRAS_CONTACTO):
            return "Contacto"
        return "No contacto"
    return _clasifica_texto(list_description)


def marcar_contactabilidad(df: pd.DataFrame,
                           col_contact: str = "contactabilidad",
                           col_desc: str = "list_description",
                           col_destino: str = "contacto") -> pd.DataFrame:
    """Agrega una columna binaria 'contacto' ('Contacto'/'No contacto')."""
    if df is None or df.empty:
        return df
    salida = df.copy()
    tiene_contact = col_contact in salida.columns
    tiene_desc = col_desc in salida.columns

    def _fila(row):
        return clasifica_contacto(
            row[col_contact] if tiene_contact else None,
            row[col_desc] if tiene_desc else None,
        )

    salida[col_destino] = salida.apply(_fila, axis=1)
    return salida


def contact_rate(df: pd.DataFrame, col_destino: str = "contacto") -> float:
    """Tasa de contactación global (0-100)."""
    if df is None or df.empty:
        return 0.0
    if col_destino not in df.columns:
        df = marcar_contactabilidad(df)
    if col_destino not in df.columns or len(df) == 0:
        return 0.0
    contactos = (df[col_destino] == "Contacto").sum()
    return round(100.0 * contactos / len(df), 1)


def contact_rate_por(df: pd.DataFrame, col_grupo: str,
                     col_destino: str = "contacto") -> pd.DataFrame:
    """Tasa de contacto agrupada por una dimensión (temporalidad, hora, etc.)."""
    if df is None or df.empty or col_grupo not in df.columns:
        return pd.DataFrame(columns=[col_grupo, "contact_rate", "intentos"])
    base = df.copy()
    if col_destino not in base.columns:
        base = marcar_contactabilidad(base)
    grp = base.groupby(col_grupo, observed=True)
    resumen = grp[col_destino].apply(
        lambda s: round(100.0 * (s == "Contacto").sum() / max(len(s), 1), 1)
    ).reset_index(name="contact_rate")
    resumen["intentos"] = grp.size().values
    return resumen
