"""Tab 1 — Cierre de Mes: recuperación vs meta, promesas, distribución."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from logic.temporalidad import ORDEN_TEMPORALIDAD, serie_ordenada_temporalidad
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
        _saldo_por_temporalidad(cartera)
    with col_d:
        _pct_por_temporalidad(cartera)

    st.divider()
    _distribucion(cartera, "segmentacion_rep", "Saldo por segmento")


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
                marker_color=COLOR_PRIMARIO, text=[moneda(kpis["recuperacion"])],
                textposition="outside")
    fig.add_bar(name="Meta", x=["Cierre"], y=[kpis["meta"]],
                marker_color="#BBBBBB", text=[moneda(kpis["meta"])],
                textposition="outside")
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
    resumen["etiqueta"] = resumen["valor_saldo_deuda"].apply(moneda)
    fig = px.bar(resumen, x=col, y="valor_saldo_deuda", title=titulo,
                 color=col, color_discrete_sequence=SECUENCIA,
                 text="etiqueta")
    fig.update_traces(textposition="outside")
    fig.update_layout(height=340, showlegend=False, margin=dict(t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)


def _resumen_temporalidad(cartera: pd.DataFrame) -> pd.DataFrame | None:
    """Saldo agrupado por temporalidad, con las 7 categorías (T1–T7) siempre."""
    if "temporalidad" not in cartera.columns:
        return None
    saldo = cartera.groupby("temporalidad")["valor_saldo_deuda"].sum()
    # Reindexa para mostrar SIEMPRE las 7 temporalidades (T1–T7), aun en 0.
    resumen = saldo.reindex(ORDEN_TEMPORALIDAD).fillna(0.0).reset_index()
    resumen.columns = ["temporalidad", "valor_saldo_deuda"]
    total = resumen["valor_saldo_deuda"].sum()
    resumen["pct"] = (100 * resumen["valor_saldo_deuda"] / total) if total else 0.0
    return resumen


def _saldo_por_temporalidad(cartera: pd.DataFrame) -> None:
    resumen = _resumen_temporalidad(cartera)
    if resumen is None:
        vacio("Sin temporalidad en la cartera.")
        return
    resumen["etiqueta"] = resumen["valor_saldo_deuda"].apply(moneda)
    fig = px.bar(resumen, x="temporalidad", y="valor_saldo_deuda",
                 title="Saldo por temporalidad (T1–T7)", color="temporalidad",
                 color_discrete_sequence=SECUENCIA, text="etiqueta")
    fig.update_traces(textposition="outside")
    fig.update_layout(height=360, showlegend=False, margin=dict(t=40, b=10),
                      xaxis_title="Temporalidad", yaxis_title="Saldo")
    st.plotly_chart(fig, use_container_width=True)


def _pct_por_temporalidad(cartera: pd.DataFrame) -> None:
    resumen = _resumen_temporalidad(cartera)
    if resumen is None:
        vacio("Sin temporalidad en la cartera.")
        return
    resumen["etiqueta"] = resumen["pct"].apply(lambda v: f"{v:.1f}%")
    fig = px.bar(resumen, x="temporalidad", y="pct",
                 title="% del saldo por temporalidad (T1–T7)",
                 color="temporalidad", color_discrete_sequence=SECUENCIA,
                 text="etiqueta")
    fig.update_traces(textposition="outside")
    fig.update_layout(height=360, showlegend=False, margin=dict(t=40, b=10),
                      xaxis_title="Temporalidad", yaxis_title="% del saldo")
    st.plotly_chart(fig, use_container_width=True)
