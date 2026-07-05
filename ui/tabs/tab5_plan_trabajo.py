"""Tab 5 — Plan de Trabajo: objetivos quincenales, metas por segmento."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from ui.common import SECUENCIA, moneda, porcentaje, vacio


def render(datos: dict, kpis: dict) -> None:
    st.subheader("🗓️ Plan de Trabajo")
    st.caption(
        "Objetivos quincenales y metas por segmento para el cierre del periodo."
    )

    recuperacion = kpis["recuperacion"]
    meta = kpis["meta"]

    # Objetivos quincenales (Q1 40% / Q2 60% de la meta).
    q1_meta, q2_meta = meta * 0.40, meta * 0.60
    q1_real = min(recuperacion, q1_meta)
    q2_real = max(recuperacion - q1_real, 0)

    quincenas = pd.DataFrame({
        "Quincena": ["Q1 (1-15)", "Q2 (16-fin)"],
        "Meta": [q1_meta, q2_meta],
        "Real": [q1_real, q2_real],
    })
    st.markdown("#### Objetivos quincenales")
    fig = px.bar(quincenas.melt(id_vars="Quincena", var_name="Tipo",
                                value_name="Monto"),
                 x="Quincena", y="Monto", color="Tipo", barmode="group",
                 color_discrete_sequence=SECUENCIA)
    fig.update_layout(height=320, margin=dict(t=20, b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.markdown("#### Metas por segmento")
    cartera = datos.get("cartera", pd.DataFrame())
    pagos = datos.get("pagos", pd.DataFrame())
    if cartera.empty or "segmentacion_rep" not in cartera.columns:
        vacio("Sin segmentación de cartera.")
    else:
        _tabla_metas_segmento(cartera, pagos)

    st.divider()
    st.markdown("#### Acciones de mejora sugeridas")
    _acciones(kpis)


def _tabla_metas_segmento(cartera: pd.DataFrame, pagos: pd.DataFrame) -> None:
    saldo = cartera.groupby("segmentacion_rep")["valor_saldo_deuda"].sum()
    if not pagos.empty and "codigo_de_cliente" in pagos.columns:
        seg_map = cartera.set_index("codigo_de_cliente")["segmentacion_rep"].to_dict()
        p = pagos.copy()
        p["segmento"] = p["codigo_de_cliente"].map(seg_map)
        recuperado = p.groupby("segmento")["pago"].sum()
    else:
        recuperado = pd.Series(dtype=float)

    tabla = pd.DataFrame({"saldo": saldo})
    tabla["meta_recuperacion"] = tabla["saldo"] * 0.35
    tabla["recuperado"] = tabla.index.map(recuperado).astype(float)
    tabla["recuperado"] = tabla["recuperado"].fillna(0.0)
    tabla["cumplimiento_%"] = (
        100 * tabla["recuperado"] / tabla["meta_recuperacion"].replace(0, pd.NA)
    ).round(1)
    tabla = tabla.reset_index().rename(columns={"segmentacion_rep": "Segmento"})

    st.dataframe(
        tabla.style.format({
            "saldo": lambda v: moneda(v),
            "meta_recuperacion": lambda v: moneda(v),
            "recuperado": lambda v: moneda(v),
            "cumplimiento_%": lambda v: porcentaje(v),
        }),
        use_container_width=True,
        hide_index=True,
    )


def _acciones(kpis: dict) -> None:
    acciones = []
    if kpis["cumplimiento_pct"] < 100:
        acciones.append(
            f"Cerrar la brecha de {moneda(kpis['brecha'])} priorizando cartera "
            "de mora temprana (T1–T3)."
        )
    if kpis["contact_rate"] < 40:
        acciones.append(
            "Reforzar horarios de mayor contactabilidad y multicanalidad "
            "(WhatsApp/SMS) para subir el contact rate."
        )
    if kpis["promesas_caidas"] > kpis["promesas_cumplidas"]:
        acciones.append(
            "Implementar recordatorios de promesa 24h antes del vencimiento "
            "para reducir promesas caídas."
        )
    if not acciones:
        acciones.append("Mantener el ritmo de gestión; indicadores en objetivo.")
    for a in acciones:
        st.markdown(f"- {a}")
