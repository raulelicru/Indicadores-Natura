"""Cruce de promesas con pagos: cumplidas, caídas, parcial vs total."""
from __future__ import annotations

import numpy as np
import pandas as pd


def _total_pagado_por_cliente(pagos: pd.DataFrame) -> pd.Series:
    if pagos is None or pagos.empty or "codigo_de_cliente" not in pagos.columns:
        return pd.Series(dtype=float)
    col_pago = "pago" if "pago" in pagos.columns else None
    if col_pago is None:
        return pd.Series(dtype=float)
    return (
        pagos.groupby("codigo_de_cliente")[col_pago]
        .sum()
        .astype(float)
    )


def cruzar_promesas_pagos(promesas: pd.DataFrame, pagos: pd.DataFrame,
                          cartera: pd.DataFrame | None = None) -> pd.DataFrame:
    """Enriquece las promesas con su cumplimiento a partir de los pagos.

    Devuelve el DataFrame de promesas con columnas adicionales:
    - ``total_pagado``: suma pagada por el cliente.
    - ``cumplida``: bool, hubo pago >= al monto de la promesa.
    - ``tipo_cumplimiento``: 'Cumplida', 'Parcial' o 'Caída'.
    - ``saldo_deuda``: saldo de cartera del cliente (si se provee cartera).
    """
    if promesas is None or promesas.empty:
        return pd.DataFrame(
            columns=[
                "codigo_de_cliente", "monto_promesa", "fecha_promesa",
                "estatus", "total_pagado", "cumplida", "tipo_cumplimiento",
            ]
        )

    out = promesas.copy()
    if "codigo_de_cliente" not in out.columns:
        out["codigo_de_cliente"] = np.nan

    pagado = _total_pagado_por_cliente(pagos)
    out["total_pagado"] = (
        out["codigo_de_cliente"].map(pagado).fillna(0.0).astype(float)
    )

    monto = pd.to_numeric(out.get("monto_promesa"), errors="coerce").fillna(0.0)

    saldo = None
    if cartera is not None and not cartera.empty and \
            {"codigo_de_cliente", "valor_saldo_deuda"}.issubset(cartera.columns):
        saldo = (
            cartera.groupby("codigo_de_cliente")["valor_saldo_deuda"]
            .sum()
            .astype(float)
        )
        out["saldo_deuda"] = (
            out["codigo_de_cliente"].map(saldo).fillna(0.0).astype(float)
        )

    def _tipo(row):
        pagado_cli = float(row["total_pagado"])
        promesa = float(row.get("monto_promesa") or 0.0)
        if pagado_cli <= 0:
            return "Caída"
        if promesa > 0 and pagado_cli + 1e-6 >= promesa:
            return "Cumplida"
        return "Parcial"

    out["tipo_cumplimiento"] = out.apply(_tipo, axis=1)
    out["cumplida"] = out["tipo_cumplimiento"] == "Cumplida"
    return out


def resumen_promesas(promesas_cruzadas: pd.DataFrame) -> dict:
    """KPIs agregados de promesas."""
    if promesas_cruzadas is None or promesas_cruzadas.empty:
        return {
            "total": 0, "cumplidas": 0, "parciales": 0, "caidas": 0,
            "monto_acordado": 0.0, "monto_recuperado": 0.0, "tasa_cumplimiento": 0.0,
        }
    total = len(promesas_cruzadas)
    cumplidas = int((promesas_cruzadas["tipo_cumplimiento"] == "Cumplida").sum())
    parciales = int((promesas_cruzadas["tipo_cumplimiento"] == "Parcial").sum())
    caidas = int((promesas_cruzadas["tipo_cumplimiento"] == "Caída").sum())
    monto_acordado = float(
        pd.to_numeric(promesas_cruzadas.get("monto_promesa"), errors="coerce")
        .fillna(0.0).sum()
    )
    # Recuperado atribuible a promesas: min(total_pagado, monto_promesa).
    monto_prom = pd.to_numeric(
        promesas_cruzadas.get("monto_promesa"), errors="coerce").fillna(0.0)
    pagado = pd.to_numeric(
        promesas_cruzadas.get("total_pagado"), errors="coerce").fillna(0.0)
    monto_recuperado = float(np.minimum(monto_prom, pagado).sum())
    tasa = round(100.0 * cumplidas / total, 1) if total else 0.0
    return {
        "total": total,
        "cumplidas": cumplidas,
        "parciales": parciales,
        "caidas": caidas,
        "monto_acordado": monto_acordado,
        "monto_recuperado": monto_recuperado,
        "tasa_cumplimiento": tasa,
    }
