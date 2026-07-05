"""Tab 6 — Comparativo Cobranza: evolución histórica por segmento/zona."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from ui.common import SECUENCIA, vacio


def render(datos: dict, kpis: dict) -> None:
    st.subheader("📈 Comparativo de Cobranza")
    comp = datos.get("comparativo", pd.DataFrame())
    if comp is None or comp.empty:
        vacio("Sin histórico comparativo (lee de kpis_cierre / archivo comparativo).")
        return

    st.caption("Evolución histórica multimés de la recuperación.")

    _evolucion(comp)
    st.divider()
    if "segmento" in comp.columns:
        _por_segmento(comp)


def _evolucion(comp: pd.DataFrame) -> None:
    agg = comp.groupby("periodo", as_index=False).agg(
        recuperacion=("recuperacion", "sum"),
        meta=("meta", "sum"),
    )
    fig = px.line(agg.melt(id_vars="periodo", var_name="Serie", value_name="Monto"),
                  x="periodo", y="Monto", color="Serie", markers=True,
                  title="Recuperación vs Meta por mes",
                  color_discrete_sequence=SECUENCIA)
    fig.update_layout(height=380, margin=dict(t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)


def _por_segmento(comp: pd.DataFrame) -> None:
    fig = px.line(comp, x="periodo", y="recuperacion", color="segmento",
                  markers=True, title="Recuperación por segmento",
                  color_discrete_sequence=SECUENCIA)
    fig.update_layout(height=380, margin=dict(t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

    pivote = comp.pivot_table(index="segmento", columns="periodo",
                              values="cumplimiento_pct", aggfunc="mean")
    st.markdown("#### Cumplimiento % por segmento y mes")
    st.dataframe(pivote.round(1), use_container_width=True)
