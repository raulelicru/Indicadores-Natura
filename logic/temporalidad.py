"""Clasificación de temporalidad (T1..T7) desde el aging de morosidad."""
from __future__ import annotations

import numpy as np
import pandas as pd

# Orden canónico de las temporalidades.
ORDEN_TEMPORALIDAD = ["T1", "T2", "T3", "T4", "T5", "T6", "T7"]

# Rangos de aging (días) por temporalidad, límite superior inclusivo.
RANGOS = [
    ("T1", 1, 30),
    ("T2", 31, 60),
    ("T3", 61, 90),
    ("T4", 91, 120),
    ("T5", 121, 150),
    ("T6", 151, 180),
    ("T7", 181, 10**9),
]


def pac_temporalidad(aging) -> str | float:
    """Devuelve la temporalidad (T1..T7) para un valor de aging de morosidad.

    - T1 = 1–30, T2 = 31–60, T3 = 61–90, T4 = 91–120,
      T5 = 121–150, T6 = 151–180, T7 = 181+.
    - Valores nulos o <= 0 devuelven ``np.nan``.
    """
    if aging is None:
        return np.nan
    try:
        dias = int(round(float(aging)))
    except (TypeError, ValueError):
        return np.nan
    if dias <= 0:
        return np.nan
    for etiqueta, minimo, maximo in RANGOS:
        if minimo <= dias <= maximo:
            return etiqueta
    return np.nan


def aplicar_temporalidad(df: pd.DataFrame, col_aging: str = "aging_de_morosidad",
                         col_destino: str = "temporalidad") -> pd.DataFrame:
    """Agrega/actualiza la columna de temporalidad a partir del aging."""
    if df is None or df.empty or col_aging not in df.columns:
        return df
    salida = df.copy()
    salida[col_destino] = salida[col_aging].apply(pac_temporalidad)
    return salida


def serie_ordenada_temporalidad(valores: pd.Series) -> pd.Categorical:
    """Convierte una serie de temporalidades en categórica ordenada T1..T7."""
    return pd.Categorical(valores, categories=ORDEN_TEMPORALIDAD, ordered=True)
