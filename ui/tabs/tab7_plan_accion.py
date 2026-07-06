"""Tab 7 — Plan de Acción Cobranza: estrategia por temporalidad."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from logic.contactabilidad import contact_rate_por, marcar_contactabilidad
from logic.temporalidad import ORDEN_TEMPORALIDAD, serie_ordenada_temporalidad
from ui.common import SECUENCIA, moneda, porcentaje, vacio

# Estrategia y tasas objetivo por temporalidad.
ESTRATEGIA = {
    "T1": ("Recordatorio amable", "Automatización SMS/WhatsApp", 85),
    "T2": ("Gestión telefónica", "Negociación de pago inmediato", 70),
    "T3": ("Gestión intensiva", "Acuerdos de pago / descuentos", 55),
    "T4": ("Escalamiento", "Plan de pagos formal", 42),
    "T5": ("Escalamiento", "Negociación con supervisor", 32),
    "T6": ("Precautela", "Última gestión amistosa", 22),
    "T7": ("Castigo/Legal", "Evaluar recuperación judicial", 12),
}


def render(datos: dict, kpis: dict) -> None:
    st.subheader("🧭 Plan de Acción de Cobranza")

    cartera = datos.get("cartera", pd.DataFrame())
    gestion = datos.get("gestion", pd.DataFrame())

    tabla = _tabla_estrategia(cartera, gestion)
    st.markdown("#### Estrategia por temporalidad y tasas objetivo")
    st.dataframe(tabla, use_container_width=True, hide_index=True)

    st.divider()
    if not cartera.empty and "temporalidad" in cartera.columns:
        _saldo_por_temporalidad(cartera)

    st.divider()
    st.markdown("#### Acciones correctivas")
    _correctivas(tabla)


def _tabla_estrategia(cartera: pd.DataFrame, gestion: pd.DataFrame) -> pd.DataFrame:
    saldo_temp = {}
    if not cartera.empty and "temporalidad" in cartera.columns:
        saldo_temp = cartera.groupby("temporalidad")["valor_saldo_deuda"].sum().to_dict()

    cr_temp = {}
    if not gestion.empty:
        g = marcar_contactabilidad(gestion)
        if "temporalidad" not in g.columns and not cartera.empty:
            mapa = cartera.set_index("codigo_de_cliente")["temporalidad"].to_dict()
            g["temporalidad"] = g["codigo_de_cliente"].map(mapa)
        res = contact_rate_por(g, "temporalidad")
        cr_temp = dict(zip(res["temporalidad"], res["contact_rate"]))

    filas = []
    for t in ORDEN_TEMPORALIDAD:
        estrategia, accion, objetivo = ESTRATEGIA[t]
        actual = cr_temp.get(t, 0.0)
        filas.append({
            "Temporalidad": t,
            "Estrategia": estrategia,
            "Acción": accion,
            "Saldo": moneda(saldo_temp.get(t, 0)),
            "Contact rate actual": porcentaje(actual),
            "Tasa objetivo": porcentaje(objetivo),
            "Brecha (pp)": round(objetivo - actual, 1),
        })
    return pd.DataFrame(filas)


def _saldo_por_temporalidad(cartera: pd.DataFrame) -> None:
    res = cartera.groupby("temporalidad")["valor_saldo_deuda"].sum().reset_index()
    res = res[res["temporalidad"].isin(ORDEN_TEMPORALIDAD)]
    res["temporalidad"] = serie_ordenada_temporalidad(res["temporalidad"])
    res = res.sort_values("temporalidad")
    fig = px.bar(res, x="temporalidad", y="valor_saldo_deuda",
                 title="Saldo en riesgo por temporalidad",
                 color="temporalidad", color_discrete_sequence=SECUENCIA,
                 text_auto=".2s")
    fig.update_traces(textposition="outside")
    fig.update_layout(height=340, showlegend=False, margin=dict(t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)


def _correctivas(tabla: pd.DataFrame) -> None:
    criticas = tabla[tabla["Brecha (pp)"] > 10].sort_values(
        "Brecha (pp)", ascending=False)
    if criticas.empty:
        st.success("Todas las temporalidades cerca de su tasa objetivo.")
        return
    for _, fila in criticas.iterrows():
        st.markdown(
            f"- **{fila['Temporalidad']}**: brecha de {fila['Brecha (pp)']} pp. "
            f"Intensificar «{fila['Acción']}»."
        )
