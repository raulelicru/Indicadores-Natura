"""Tab 9 — Operación (consolidado).

Gestión (Vici), distribución por canal, top 10 asesores con % de contactación,
acuerdos realizados vs cumplidos por día.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from logic.contactabilidad import marcar_contactabilidad
from ui.common import COLOR_OK, COLOR_PRIMARIO, SECUENCIA, porcentaje, vacio


def render(datos: dict, kpis: dict) -> None:
    st.subheader("🛠️ Operación — Consolidado")
    gestion = datos.get("gestion", pd.DataFrame())
    promesas = kpis.get("promesas_cruzadas", pd.DataFrame())

    if gestion.empty:
        vacio("Sin datos de gestión (Vici).")
        return

    g = marcar_contactabilidad(gestion)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gestiones (Vici)", f"{len(g):,}")
    c2.metric("Contactos", f"{int((g['contacto']=='Contacto').sum()):,}")
    c3.metric("Contact rate", porcentaje(round(100*(g['contacto']=='Contacto').mean(), 1)))
    c4.metric("Asesores activos", f"{g['asesor'].nunique() if 'asesor' in g else 0}")

    st.divider()
    col_a, col_b = st.columns([1, 1])
    with col_a:
        _distribucion_canal(g)
    with col_b:
        _top_asesores_contactacion(g)

    st.divider()
    st.markdown("#### Acuerdos realizados vs cumplidos por día")
    _acuerdos_por_dia(promesas)


def _distribucion_canal(g: pd.DataFrame) -> None:
    if "canal" not in g.columns:
        vacio("Sin canal.")
        return
    res = g["canal"].value_counts().reset_index()
    res.columns = ["canal", "conteo"]
    fig = px.bar(res, x="canal", y="conteo", color="canal",
                 title="Distribución por canal",
                 color_discrete_sequence=SECUENCIA)
    fig.update_layout(height=360, showlegend=False, margin=dict(t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)


def _top_asesores_contactacion(g: pd.DataFrame) -> None:
    if "asesor" not in g.columns:
        vacio("Sin asesor.")
        return
    grp = g.groupby("asesor")
    res = pd.DataFrame({
        "gestiones": grp.size(),
        "contactacion": grp["contacto"].apply(
            lambda s: round(100 * (s == "Contacto").mean(), 1)),
    }).reset_index()
    res = res.sort_values("gestiones", ascending=False).head(10)
    fig = go.Figure()
    fig.add_bar(x=res["asesor"], y=res["gestiones"], name="Gestiones",
                marker_color=COLOR_PRIMARIO, yaxis="y")
    fig.add_trace(go.Scatter(
        x=res["asesor"], y=res["contactacion"], name="% contactación",
        mode="lines+markers", marker_color=COLOR_OK, yaxis="y2",
    ))
    fig.update_layout(
        title="Top 10 asesores: volumen y % contactación",
        height=360, margin=dict(t=40, b=10),
        yaxis=dict(title="Gestiones"),
        yaxis2=dict(title="% contactación", overlaying="y", side="right",
                    range=[0, 100]),
        legend=dict(orientation="h", y=1.12),
    )
    st.plotly_chart(fig, use_container_width=True)


def _acuerdos_por_dia(promesas: pd.DataFrame) -> None:
    if promesas is None or promesas.empty or "fecha_promesa" not in promesas.columns:
        vacio("Sin promesas con fecha para el consolidado diario.")
        return
    p = promesas.dropna(subset=["fecha_promesa"]).copy()
    if p.empty:
        vacio("Sin fechas de promesa válidas.")
        return
    p["dia"] = pd.to_datetime(p["fecha_promesa"]).dt.date
    realizados = p.groupby("dia").size()
    cumplidos = p[p["tipo_cumplimiento"] == "Cumplida"].groupby("dia").size()
    res = pd.DataFrame({
        "Realizados": realizados,
        "Cumplidos": cumplidos,
    }).fillna(0).reset_index()
    fig = px.bar(res.melt(id_vars="dia", var_name="Tipo", value_name="Conteo"),
                 x="dia", y="Conteo", color="Tipo", barmode="group",
                 color_discrete_sequence=[COLOR_PRIMARIO, COLOR_OK])
    fig.update_layout(height=360, margin=dict(t=20, b=10))
    st.plotly_chart(fig, use_container_width=True)
