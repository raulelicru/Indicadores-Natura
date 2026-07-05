"""Tab 1 — Cierre de Mes: recuperación vs meta, promesas, distribución."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ui.common import (
    COLOR_ALERTA,
    COLOR_OK,
    COLOR_PRIMARIO,
    SECUENCIA,
    moneda,
    porcentaje,
    vacio,
)


def render(datos: dict, kpis: dict) -> None:
    st.subheader("🎯 Cierre de Mes")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Recuperación", moneda(kpis["recuperacion"]))
    c2.metric("Meta", moneda(kpis["meta"]))
    c3.metric("Cumplimiento", porcentaje(kpis["cumplimiento_pct"]),
              delta=porcentaje(kpis["cumplimiento_pct"] - 100))
    c4.metric("Brecha", moneda(kpis["brecha"]))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Promesas generadas", f"{kpis['promesas_generadas']:,}")
    c6.metric("Promesas caídas", f"{kpis['promesas_caidas']:,}")
    c7.metric("Clientes en cartera", f"{kpis['clientes']:,}")
    c8.metric("Contact rate", porcentaje(kpis["contact_rate"]))

    st.divider()

    col_a, col_b = st.columns([1, 1])
    with col_a:
        _gauge_cumplimiento(kpis)
    with col_b:
        _recuperacion_vs_meta(kpis)

    st.divider()
    cartera = datos.get("cartera", pd.DataFrame())
    if cartera.empty:
        vacio("Sin datos de cartera para distribución.")
        return

    col_c, col_d = st.columns(2)
    with col_c:
        _distribucion(cartera, "segmentacion_rep", "Saldo por segmento")
    with col_d:
        _distribucion(cartera, "zona", "Saldo por zona")


def _gauge_cumplimiento(kpis: dict) -> None:
    valor = kpis["cumplimiento_pct"]
    color = COLOR_OK if valor >= 100 else (COLOR_PRIMARIO if valor >= 80 else COLOR_ALERTA)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valor,
        number={"suffix": "%"},
        title={"text": "Cumplimiento de meta"},
        gauge={
            "axis": {"range": [0, 140]},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 80], "color": "#F8D7DA"},
                {"range": [80, 100], "color": "#FFF3CD"},
                {"range": [100, 140], "color": "#D4EDDA"},
            ],
        },
    ))
    fig.update_layout(height=300, margin=dict(t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)


def _recuperacion_vs_meta(kpis: dict) -> None:
    fig = go.Figure()
    fig.add_bar(name="Recuperado", x=["Cierre"], y=[kpis["recuperacion"]],
                marker_color=COLOR_PRIMARIO)
    fig.add_bar(name="Meta", x=["Cierre"], y=[kpis["meta"]],
                marker_color="#BBBBBB")
    fig.update_layout(barmode="group", height=300, title="Recuperación vs Meta",
                      margin=dict(t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)


def _distribucion(cartera: pd.DataFrame, col: str, titulo: str) -> None:
    if col not in cartera.columns:
        vacio(f"Sin columna {col}.")
        return
    resumen = (
        cartera.groupby(col)["valor_saldo_deuda"].sum()
        .sort_values(ascending=False).reset_index()
    )
    fig = px.bar(resumen, x=col, y="valor_saldo_deuda", title=titulo,
                 color=col, color_discrete_sequence=SECUENCIA)
    fig.update_layout(height=340, showlegend=False, margin=dict(t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)
