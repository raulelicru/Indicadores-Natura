"""Helpers compartidos por las pestañas: formato, KPIs y paleta."""
from __future__ import annotations

import numpy as np
import pandas as pd

from logic.contactabilidad import contact_rate, marcar_contactabilidad
from logic.promesas import cruzar_promesas_pagos, resumen_promesas

# Paleta corporativa Natura.
COLOR_PRIMARIO = "#E4002B"
COLOR_SECUNDARIO = "#F5A623"
COLOR_OK = "#2E9E5B"
COLOR_ALERTA = "#D64545"
SECUENCIA = ["#E4002B", "#F5A623", "#2E9E5B", "#3F7CAC", "#8E44AD",
             "#16A085", "#E67E22"]


def moneda(valor) -> str:
    try:
        return f"${float(valor):,.0f}"
    except (TypeError, ValueError):
        return "$0"


def porcentaje(valor, decimales: int = 1) -> str:
    try:
        return f"{float(valor):.{decimales}f}%"
    except (TypeError, ValueError):
        return "0%"


def calcular_kpis(datos: dict) -> dict:
    """Calcula el bloque de KPIs de cierre a partir del dataset."""
    cartera = datos.get("cartera", pd.DataFrame())
    pagos = datos.get("pagos", pd.DataFrame())
    gestion = datos.get("gestion", pd.DataFrame())
    promesas = datos.get("promesas", pd.DataFrame())

    recuperacion = float(
        pd.to_numeric(pagos.get("pago"), errors="coerce").fillna(0).sum()
    ) if not pagos.empty else 0.0

    saldo_total = float(
        pd.to_numeric(cartera.get("valor_saldo_deuda"), errors="coerce")
        .fillna(0).sum()
    ) if not cartera.empty else 0.0

    # Meta: por defecto 105% de lo recuperado si no hay meta explícita.
    meta = datos.get("meta")
    if meta is None:
        meta = max(recuperacion * 1.12, saldo_total * 0.35, 1.0)
    cumplimiento = round(100 * recuperacion / meta, 1) if meta else 0.0
    brecha = meta - recuperacion

    cr = contact_rate(marcar_contactabilidad(gestion)) if not gestion.empty else 0.0

    prom_cruz = cruzar_promesas_pagos(promesas, pagos, cartera)
    rp = resumen_promesas(prom_cruz)

    return {
        "recuperacion": recuperacion,
        "meta": meta,
        "cumplimiento_pct": cumplimiento,
        "brecha": brecha,
        "saldo_total": saldo_total,
        "contact_rate": cr,
        "promesas_generadas": rp["total"],
        "promesas_cumplidas": rp["cumplidas"],
        "promesas_caidas": rp["caidas"],
        "promesas_parciales": rp["parciales"],
        "monto_acordado": rp["monto_acordado"],
        "monto_recuperado_promesas": rp["monto_recuperado"],
        "tasa_cumplimiento_promesas": rp["tasa_cumplimiento"],
        "promesas_cruzadas": prom_cruz,
        "clientes": int(cartera["codigo_de_cliente"].nunique())
                    if not cartera.empty else 0,
    }


def vacio(mensaje: str = "No hay datos para mostrar en este periodo."):
    import streamlit as st
    st.info(mensaje)
