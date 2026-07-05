"""Dashboard Ejecutivo de Cobranza Natura — entry point.

Router de autenticación + render de pestañas. Soporta modo demostración
(datos sintéticos) y modo real (carga → normalización → persistencia en
Supabase con RLS).
"""
from __future__ import annotations

import streamlit as st

from auth.roles import cargar_perfil, es_admin, puede_cargar, rol_actual
from auth.session import (
    cerrar_sesion,
    refrescar_si_necesario,
    sesion_valida,
)
from db.client import credenciales_configuradas, demo_habilitado

st.set_page_config(
    page_title="Cobranza Natura",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

PERIODO_DEFECTO = "2025-06"


# ---------------------------------------------------------------------------
# Utilidades de datos
# ---------------------------------------------------------------------------
def _cargar_dataset_demo(periodo: str) -> dict:
    from demo.synthetic import generar_dataset
    return generar_dataset(periodo)


def _cargar_dataset_real(periodo: str) -> dict:
    from db.readers import cargar_dataset
    user_id = st.session_state.get("user_id")
    try:
        return cargar_dataset(user_id, periodo)
    except Exception as exc:  # noqa: BLE001
        st.error(f"No se pudieron leer los datos del periodo: {exc}")
        return {"periodo": periodo, "modo": "real", "cartera": None,
                "pagos": None, "gestion": None, "promesas": None,
                "comparativo": None}


def _dataset_vacio(datos: dict) -> bool:
    import pandas as pd
    for k in ("cartera", "pagos", "gestion", "promesas"):
        df = datos.get(k)
        if isinstance(df, pd.DataFrame) and not df.empty:
            return False
    return True


# ---------------------------------------------------------------------------
# Modo demo
# ---------------------------------------------------------------------------
def _render_demo() -> None:
    from ui.tabs import render_tabs

    with st.sidebar:
        st.markdown("### 💎 Cobranza Natura")
        st.info("Modo demostración (datos sintéticos)")
        periodo = st.text_input("Periodo", value=PERIODO_DEFECTO)
        if credenciales_configuradas():
            if st.button("Salir del demo", use_container_width=True):
                st.session_state["modo_demo"] = False
                st.rerun()

    st.title("💎 Dashboard Ejecutivo de Cobranza")
    st.caption("Modo demostración — los datos no se guardan en la base de datos.")
    datos = _cargar_dataset_demo(periodo or PERIODO_DEFECTO)
    render_tabs(datos)


# ---------------------------------------------------------------------------
# Modo real (autenticado)
# ---------------------------------------------------------------------------
def _render_sidebar(perfil: dict) -> tuple[str, str]:
    with st.sidebar:
        st.markdown("### 💎 Cobranza Natura")
        st.write(f"**{perfil.get('nombre') or st.session_state.get('user_email')}**")
        st.caption(f"Rol: {rol_actual()}")

        periodo = st.text_input("Periodo (AAAA-MM)", value=PERIODO_DEFECTO,
                                key="periodo_sel")

        vista = "Dashboard"
        opciones = ["Dashboard"]
        if puede_cargar():
            opciones.append("Cargar archivos")
        if es_admin():
            opciones.append("Administrar usuarios")
        vista = st.radio("Vista", opciones, label_visibility="collapsed")

        st.divider()
        if st.button("🚪 Cerrar sesión", use_container_width=True):
            cerrar_sesion()
    return periodo, vista


def _procesar_y_persistir(datos_norm: dict, periodo: str) -> None:
    """Persiste el dataset cargado y lo deja disponible para las pestañas."""
    from db.writers import guardar_kpis_cierre, persistir_dataset
    from ui.common import calcular_kpis

    user_id = st.session_state.get("user_id")
    nombres = st.session_state.get("nombres_archivos", {})
    with st.spinner("Guardando datos en la base…"):
        try:
            resumen = persistir_dataset(user_id, periodo, datos_norm, nombres)
        except Exception as exc:  # noqa: BLE001
            st.error(f"No se pudieron guardar los datos: {exc}")
            return
        # Snapshot de KPIs de cierre.
        try:
            kpis = calcular_kpis(datos_norm)
            guardar_kpis_cierre(user_id, periodo, {
                "recuperacion": kpis["recuperacion"],
                "meta": kpis["meta"],
                "cumplimiento_pct": kpis["cumplimiento_pct"],
                "contact_rate": kpis["contact_rate"],
                "promesas_generadas": kpis["promesas_generadas"],
                "promesas_caidas": kpis["promesas_caidas"],
            })
        except Exception:  # noqa: BLE001
            pass
    total = sum(resumen.values()) if resumen else 0
    st.success(f"Datos guardados: {total:,} filas en {len(resumen)} tablas.")
    st.session_state["dataset"] = datos_norm
    st.session_state["vista_forzada"] = "Dashboard"


def _render_real() -> None:
    from ui.admin_view import render_admin
    from ui.tabs import render_tabs
    from ui.welcome_view import render_welcome

    perfil = cargar_perfil()
    periodo, vista = _render_sidebar(perfil)

    st.title("💎 Dashboard Ejecutivo de Cobranza")

    if vista == "Administrar usuarios":
        render_admin()
        return

    if vista == "Cargar archivos":
        datos_norm = render_welcome(st.session_state.get("user_id"), periodo)
        if datos_norm is not None:
            _procesar_y_persistir(datos_norm, periodo)
            st.rerun()
        return

    # Vista Dashboard: usa dataset en sesión o lo reconstruye desde Postgres.
    datos = st.session_state.get("dataset")
    if not datos or datos.get("periodo") != periodo:
        with st.spinner("Cargando datos del periodo…"):
            datos = _cargar_dataset_real(periodo)
        st.session_state["dataset"] = datos

    if _dataset_vacio(datos):
        st.info(
            f"No hay datos cargados para el periodo **{periodo}**."
        )
        if puede_cargar():
            st.caption("Usa **Cargar archivos** en el menú lateral para comenzar.")
        return

    render_tabs(datos)


# ---------------------------------------------------------------------------
# Router principal
# ---------------------------------------------------------------------------
def main() -> None:
    # Modo demo explícito.
    if st.session_state.get("modo_demo") and demo_habilitado():
        _render_demo()
        return

    # Sin credenciales configuradas: solo demo disponible.
    if not credenciales_configuradas():
        if demo_habilitado():
            _render_demo()
        else:
            from ui.login_view import render_login
            render_login()
        return

    # Refresca token si está por expirar (transparente).
    if sesion_valida():
        refrescar_si_necesario()

    if not sesion_valida():
        from ui.login_view import render_login
        render_login()
        return

    _render_real()


if __name__ == "__main__":
    main()
