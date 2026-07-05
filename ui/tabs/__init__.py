"""Orquestador de las 9 pestañas del dashboard."""
from __future__ import annotations

import streamlit as st

from ui.common import calcular_kpis
from ui.tabs import (
    tab1_cierre,
    tab2_contactabilidad,
    tab3_indicadores,
    tab4_operacion,
    tab5_plan_trabajo,
    tab6_comparativo,
    tab7_plan_accion,
    tab8_indicadores_cierre,
    tab9_operacion_consolidado,
)

TABS = [
    ("Cierre de Mes", tab1_cierre.render),
    ("Contactabilidad", tab2_contactabilidad.render),
    ("Indicadores", tab3_indicadores.render),
    ("Operación", tab4_operacion.render),
    ("Plan de Trabajo", tab5_plan_trabajo.render),
    ("Comparativo Cobranza", tab6_comparativo.render),
    ("Plan de Acción", tab7_plan_accion.render),
    ("Indicadores Cierre", tab8_indicadores_cierre.render),
    ("Operación (Consolidado)", tab9_operacion_consolidado.render),
]


def render_tabs(datos: dict) -> None:
    """Calcula KPIs y renderiza las 9 pestañas."""
    kpis = calcular_kpis(datos)
    st.session_state["kpis_actuales"] = {
        k: v for k, v in kpis.items() if k != "promesas_cruzadas"
    }
    nombres = [n for n, _ in TABS]
    contenedores = st.tabs(nombres)
    for contenedor, (_, render_fn) in zip(contenedores, TABS):
        with contenedor:
            try:
                render_fn(datos, kpis)
            except Exception as exc:  # noqa: BLE001
                st.error(f"No se pudo renderizar esta pestaña: {exc}")
