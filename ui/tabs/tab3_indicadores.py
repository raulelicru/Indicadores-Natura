"""Tab 3 — Indicadores: promesas total, cumplidas, acordado vs recuperado."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ui.common import COLOR_OK, COLOR_PRIMARIO, SECUENCIA, moneda, porcentaje, vacio


def render(datos: dict, kpis: dict) -> None:
    st.subheader("📊 Indicadores de Promesas")
    prom = kpis.get("promesas_cruzadas", pd.DataFrame())
    if prom is None or prom.empty:
        vacio("Sin promesas registradas en el periodo.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Promesas totales", f"{kpis['promesas_generadas']:,}")
    c2.metric("Cumplidas", f"{kpis['promesas_cumplidas']:,}")
    c3.metric("Parciales", f"{kpis['promesas_parciales']:,}")
    c4.metric("Caídas", f"{kpis['promesas_caidas']:,}")

    c5, c6, c7 = st.columns(3)
    c5.metric("Tasa de cumplimiento", porcentaje(kpis["tasa_cumplimiento_promesas"]))
    c6.metric("Monto acordado", moneda(kpis["monto_acordado"]))
    c7.metric("Monto recuperado", moneda(kpis["monto_recuperado_promesas"]))

    st.divider()
    col_a, col_b = st.columns([1, 1])
    with col_a:
        _dona_tipo(prom)
    with col_b:
        _acordado_vs_recuperado(kpis)


def _dona_tipo(prom: pd.DataFrame) -> None:
    res = prom["tipo_cumplimiento"].value_counts().reset_index()
    res.columns = ["tipo", "conteo"]
    fig = px.pie(res, names="tipo", values="conteo", hole=0.5,
                 title="Distribución de promesas",
                 color_discrete_sequence=SECUENCIA)
    fig.update_layout(height=360, margin=dict(t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)


def _acordado_vs_recuperado(kpis: dict) -> None:
    fig = go.Figure()
    fig.add_bar(name="Acordado", x=["Promesas"], y=[kpis["monto_acordado"]],
                marker_color="#BBBBBB")
    fig.add_bar(name="Recuperado", x=["Promesas"],
                y=[kpis["monto_recuperado_promesas"]], marker_color=COLOR_OK)
    fig.update_layout(barmode="group", height=360,
                      title="Monto acordado vs recuperado",
                      margin=dict(t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)
