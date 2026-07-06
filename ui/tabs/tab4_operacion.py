"""Tab 4 — Operación: llamadas, SMS, intentos promedio, canal y asesor."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from ui.common import SECUENCIA, vacio


def render(datos: dict, kpis: dict) -> None:
    st.subheader("⚙️ Operación de Gestión")
    gestion = datos.get("gestion", pd.DataFrame())
    if gestion.empty:
        vacio("Sin datos de gestión.")
        return

    total = len(gestion)
    clientes = gestion["codigo_de_cliente"].nunique() if \
        "codigo_de_cliente" in gestion.columns else 0
    intentos_prom = round(total / clientes, 2) if clientes else 0.0
    sms = int((gestion.get("canal") == "SMS").sum()) if "canal" in gestion.columns else 0
    llamadas = int((gestion.get("canal") == "Llamada").sum()) if \
        "canal" in gestion.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gestiones totales", f"{total:,}")
    c2.metric("Llamadas", f"{llamadas:,}")
    c3.metric("SMS", f"{sms:,}")
    c4.metric("Intentos promedio / cliente", f"{intentos_prom}")

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        _por_canal(gestion)
    with col_b:
        _por_asesor(gestion)

    if "duracion_seg" in gestion.columns:
        st.divider()
        _duracion(gestion)


def _por_canal(gestion: pd.DataFrame) -> None:
    if "canal" not in gestion.columns:
        vacio("Sin columna canal.")
        return
    res = gestion["canal"].value_counts().reset_index()
    res.columns = ["canal", "conteo"]
    fig = px.pie(res, names="canal", values="conteo", hole=0.45,
                 title="Distribución por canal",
                 color_discrete_sequence=SECUENCIA)
    fig.update_traces(texttemplate="%{label}<br>%{value} (%{percent})")
    fig.update_layout(height=360, margin=dict(t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)


def _por_asesor(gestion: pd.DataFrame) -> None:
    if "asesor" not in gestion.columns:
        vacio("Sin columna asesor.")
        return
    res = gestion["asesor"].value_counts().reset_index().head(10)
    res.columns = ["asesor", "gestiones"]
    fig = px.bar(res, x="gestiones", y="asesor", orientation="h",
                 title="Gestiones por asesor (top 10)",
                 color_discrete_sequence=SECUENCIA, text="gestiones")
    fig.update_traces(textposition="outside")
    fig.update_layout(height=360, margin=dict(t=40, b=10),
                      yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)


def _duracion(gestion: pd.DataFrame) -> None:
    dur = pd.to_numeric(gestion["duracion_seg"], errors="coerce").dropna()
    dur = dur[dur > 0]
    if dur.empty:
        return
    fig = px.histogram(dur, nbins=30, title="Distribución de duración de llamadas (seg)",
                       color_discrete_sequence=SECUENCIA)
    fig.update_layout(height=320, showlegend=False, margin=dict(t=40, b=10),
                      xaxis_title="Segundos", yaxis_title="Llamadas")
    st.plotly_chart(fig, use_container_width=True)
