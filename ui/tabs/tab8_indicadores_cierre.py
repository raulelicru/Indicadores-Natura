"""Tab 8 — Indicadores Cierre de Mes (maestra).

Sub-tabs: Asignación, Recuperación, Gestión, Operación.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from logic.contactabilidad import contact_rate_por, marcar_contactabilidad
from logic.temporalidad import ORDEN_TEMPORALIDAD, serie_ordenada_temporalidad
from ui.common import SECUENCIA, moneda, porcentaje, vacio


def render(datos: dict, kpis: dict) -> None:
    st.subheader("📋 Indicadores Cierre de Mes")
    sub_asig, sub_rec, sub_gest, sub_oper = st.tabs(
        ["Asignación", "Recuperación", "Gestión", "Operación"]
    )
    with sub_asig:
        _asignacion(datos)
    with sub_rec:
        _recuperacion(datos, kpis)
    with sub_gest:
        _gestion(datos)
    with sub_oper:
        _operacion(datos, kpis)


def _asignacion(datos: dict) -> None:
    cartera = datos.get("cartera", pd.DataFrame())
    if cartera.empty:
        vacio("Sin cartera asignada.")
        return
    c1, c2, c3 = st.columns(3)
    c1.metric("Clientes asignados", f"{cartera['codigo_de_cliente'].nunique():,}")
    c2.metric("Saldo total asignado",
              moneda(cartera["valor_saldo_deuda"].sum()))
    c3.metric("Ticket promedio",
              moneda(cartera["valor_saldo_deuda"].mean()))

    col_a, col_b = st.columns(2)
    with col_a:
        if "temporalidad" in cartera.columns:
            res = cartera.groupby("temporalidad")["codigo_de_cliente"].nunique()
            res = res.reindex(ORDEN_TEMPORALIDAD).fillna(0).reset_index()
            res.columns = ["temporalidad", "clientes"]
            fig = px.bar(res, x="temporalidad", y="clientes",
                         title="Clientes asignados por temporalidad",
                         color_discrete_sequence=SECUENCIA)
            fig.update_layout(height=340, margin=dict(t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)
    with col_b:
        if "zona" in cartera.columns:
            res = cartera.groupby("zona")["valor_saldo_deuda"].sum().reset_index()
            fig = px.bar(res, x="zona", y="valor_saldo_deuda",
                         title="Saldo asignado por zona", color="zona",
                         color_discrete_sequence=SECUENCIA)
            fig.update_layout(height=340, showlegend=False, margin=dict(t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)


def _recuperacion(datos: dict, kpis: dict) -> None:
    c1, c2, c3 = st.columns(3)
    c1.metric("Recuperado", moneda(kpis["recuperacion"]))
    c2.metric("Meta", moneda(kpis["meta"]))
    c3.metric("Cumplimiento", porcentaje(kpis["cumplimiento_pct"]))

    cartera = datos.get("cartera", pd.DataFrame())
    pagos = datos.get("pagos", pd.DataFrame())
    if pagos.empty:
        vacio("Sin pagos registrados.")
        return

    if not cartera.empty and "temporalidad" in cartera.columns:
        mapa = cartera.set_index("codigo_de_cliente")["temporalidad"].to_dict()
        p = pagos.copy()
        p["temporalidad"] = p["codigo_de_cliente"].map(mapa)
        res = p.groupby("temporalidad")["pago"].sum().reindex(
            ORDEN_TEMPORALIDAD).fillna(0).reset_index()
        fig = px.bar(res, x="temporalidad", y="pago",
                     title="Recuperación por temporalidad",
                     color_discrete_sequence=SECUENCIA)
        fig.update_layout(height=360, margin=dict(t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    if "fecha_pago" in pagos.columns:
        serie = pagos.dropna(subset=["fecha_pago"]).copy()
        serie["dia"] = pd.to_datetime(serie["fecha_pago"]).dt.date
        diario = serie.groupby("dia")["pago"].sum().cumsum().reset_index()
        fig = px.area(diario, x="dia", y="pago",
                      title="Recuperación acumulada en el mes",
                      color_discrete_sequence=SECUENCIA)
        fig.update_layout(height=340, margin=dict(t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)


def _gestion(datos: dict) -> None:
    gestion = datos.get("gestion", pd.DataFrame())
    if gestion.empty:
        vacio("Sin gestión.")
        return
    g = marcar_contactabilidad(gestion)
    c1, c2, c3 = st.columns(3)
    c1.metric("Gestiones", f"{len(g):,}")
    c2.metric("Contactos", f"{int((g['contacto']=='Contacto').sum()):,}")
    cr = round(100 * (g["contacto"] == "Contacto").mean(), 1)
    c3.metric("Contact rate", porcentaje(cr))

    cartera = datos.get("cartera", pd.DataFrame())
    if not cartera.empty:
        mapa = cartera.set_index("codigo_de_cliente")["temporalidad"].to_dict()
        g["temporalidad"] = g["codigo_de_cliente"].map(mapa)
        res = contact_rate_por(g, "temporalidad")
        res = res[res["temporalidad"].isin(ORDEN_TEMPORALIDAD)]
        res["temporalidad"] = serie_ordenada_temporalidad(res["temporalidad"])
        res = res.sort_values("temporalidad")
        fig = px.bar(res, x="temporalidad", y="contact_rate",
                     title="Contact rate por temporalidad",
                     color_discrete_sequence=SECUENCIA)
        fig.update_layout(height=360, margin=dict(t=40, b=10), yaxis_title="%")
        st.plotly_chart(fig, use_container_width=True)


def _operacion(datos: dict, kpis: dict) -> None:
    gestion = datos.get("gestion", pd.DataFrame())
    if gestion.empty:
        vacio("Sin operación.")
        return
    c1, c2 = st.columns(2)
    if "canal" in gestion.columns:
        with c1:
            res = gestion["canal"].value_counts().reset_index()
            res.columns = ["canal", "conteo"]
            fig = px.pie(res, names="canal", values="conteo", hole=0.45,
                         title="Gestiones por canal",
                         color_discrete_sequence=SECUENCIA)
            fig.update_layout(height=340, margin=dict(t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)
    if "asesor" in gestion.columns:
        with c2:
            res = gestion["asesor"].value_counts().reset_index().head(10)
            res.columns = ["asesor", "gestiones"]
            fig = px.bar(res, x="gestiones", y="asesor", orientation="h",
                         title="Top asesores por volumen",
                         color_discrete_sequence=SECUENCIA)
            fig.update_layout(height=340, margin=dict(t=40, b=10),
                              yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)
