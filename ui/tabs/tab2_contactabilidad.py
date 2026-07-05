"""Tab 2 — Contactabilidad: general, por temporalidad, hora, camino, asesores."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from logic.contactabilidad import contact_rate, contact_rate_por, marcar_contactabilidad
from logic.temporalidad import ORDEN_TEMPORALIDAD, serie_ordenada_temporalidad
from ui.common import COLOR_PRIMARIO, SECUENCIA, porcentaje, vacio


def render(datos: dict, kpis: dict) -> None:
    st.subheader("📞 Contactabilidad")
    gestion = datos.get("gestion", pd.DataFrame())
    cartera = datos.get("cartera", pd.DataFrame())
    if gestion.empty:
        vacio("Sin datos de gestión.")
        return

    g = marcar_contactabilidad(gestion)
    cr = contact_rate(g)

    c1, c2, c3 = st.columns(3)
    c1.metric("Contact rate general", porcentaje(cr))
    c2.metric("Intentos de gestión", f"{len(g):,}")
    c3.metric("Contactos efectivos", f"{int((g['contacto']=='Contacto').sum()):,}")

    st.divider()

    # Enriquecer con temporalidad desde cartera si es posible.
    if not cartera.empty and "temporalidad" in cartera.columns:
        mapa_temp = cartera.set_index("codigo_de_cliente")["temporalidad"].to_dict()
        g["temporalidad"] = g["codigo_de_cliente"].map(mapa_temp)

    col_a, col_b = st.columns(2)
    with col_a:
        _por_temporalidad(g)
    with col_b:
        _por_hora(g)

    st.divider()
    col_c, col_d = st.columns(2)
    with col_c:
        _por_camino(g, cartera)
    with col_d:
        _top_asesores(g)


def _por_temporalidad(g: pd.DataFrame) -> None:
    if "temporalidad" not in g.columns or g["temporalidad"].isna().all():
        vacio("Sin temporalidad asociada.")
        return
    res = contact_rate_por(g, "temporalidad")
    res = res[res["temporalidad"].isin(ORDEN_TEMPORALIDAD)]
    res["temporalidad"] = serie_ordenada_temporalidad(res["temporalidad"])
    res = res.sort_values("temporalidad")
    fig = px.bar(res, x="temporalidad", y="contact_rate",
                 title="Contact rate por temporalidad (T1–T7)",
                 text="contact_rate", color_discrete_sequence=[COLOR_PRIMARIO])
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(height=340, margin=dict(t=40, b=10), yaxis_title="%")
    st.plotly_chart(fig, use_container_width=True)


def _por_hora(g: pd.DataFrame) -> None:
    if "hora_llamada" not in g.columns:
        vacio("Sin hora de llamada.")
        return
    tmp = g.copy()
    tmp["hora"] = tmp["hora_llamada"].astype(str).str.slice(0, 2)
    res = contact_rate_por(tmp, "hora").sort_values("hora")
    fig = px.line(res, x="hora", y="contact_rate", markers=True,
                  title="Contact rate por hora",
                  color_discrete_sequence=[COLOR_PRIMARIO])
    fig.update_layout(height=340, margin=dict(t=40, b=10), yaxis_title="%")
    st.plotly_chart(fig, use_container_width=True)


def _por_camino(g: pd.DataFrame, cartera: pd.DataFrame) -> None:
    if cartera.empty or "rango_edad_consultora" not in cartera.columns:
        vacio("Sin camino de crecimiento.")
        return
    mapa = cartera.set_index("codigo_de_cliente")["rango_edad_consultora"].to_dict()
    tmp = g.copy()
    tmp["camino"] = tmp["codigo_de_cliente"].map(mapa)
    res = contact_rate_por(tmp, "camino").dropna(subset=["camino"])
    fig = px.bar(res, x="camino", y="contact_rate", color="camino",
                 title="Contact rate por camino de crecimiento",
                 color_discrete_sequence=SECUENCIA)
    fig.update_layout(height=340, showlegend=False, margin=dict(t=40, b=10),
                      yaxis_title="%")
    st.plotly_chart(fig, use_container_width=True)


def _top_asesores(g: pd.DataFrame) -> None:
    if "asesor" not in g.columns:
        vacio("Sin asesor.")
        return
    res = contact_rate_por(g, "asesor").sort_values("contact_rate", ascending=False)
    res = res.head(10)
    fig = px.bar(res, x="contact_rate", y="asesor", orientation="h",
                 title="Top asesores por contact rate",
                 text="contact_rate", color_discrete_sequence=[COLOR_PRIMARIO])
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(height=380, margin=dict(t=40, b=10),
                      yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)
