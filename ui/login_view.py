"""Pantalla de login / registro / magic link."""
from __future__ import annotations

import streamlit as st

from auth.session import (
    enviar_magic_link,
    iniciar_sesion,
    registrar,
)
from db.client import credenciales_configuradas, demo_habilitado


def _encabezado() -> None:
    st.markdown(
        "<h1 style='margin-bottom:0'>💎 Cobranza Natura</h1>"
        "<p style='color:#666;margin-top:4px'>Dashboard ejecutivo de cierre de mes</p>",
        unsafe_allow_html=True,
    )


def render_login() -> None:
    """Renderiza el login. Bloquea el resto de la app hasta autenticar."""
    _encabezado()

    if not credenciales_configuradas():
        st.info(
            "No hay credenciales de Supabase configuradas. Puedes explorar la "
            "aplicación en **modo demostración** con datos sintéticos."
        )
        if demo_habilitado():
            if st.button("🚀 Entrar en modo demostración", type="primary",
                         use_container_width=True):
                st.session_state["modo_demo"] = True
                st.rerun()
        return

    col_izq, _ = st.columns([1, 1])
    with col_izq:
        tab_login, tab_registro = st.tabs(["Iniciar sesión", "Registrarme"])

        with tab_login:
            _formulario_login()

        with tab_registro:
            _formulario_registro()

        if demo_habilitado():
            st.divider()
            if st.button("Explorar en modo demostración", use_container_width=True):
                st.session_state["modo_demo"] = True
                st.rerun()


def _formulario_login() -> None:
    usar_magic = st.toggle("Usar enlace mágico (sin contraseña)", value=False,
                           key="toggle_magic")
    with st.form("form_login"):
        email = st.text_input("Correo", key="login_email")
        if not usar_magic:
            password = st.text_input("Contraseña", type="password",
                                     key="login_pass")
        else:
            password = None
        enviado = st.form_submit_button("Entrar", type="primary",
                                        use_container_width=True)
    if enviado:
        if usar_magic:
            ok, msg = enviar_magic_link(email)
            (st.success if ok else st.error)(msg)
        else:
            ok, msg = iniciar_sesion(email, password or "")
            if ok:
                st.session_state["modo_demo"] = False
                st.rerun()
            else:
                st.error(msg)


def _formulario_registro() -> None:
    with st.form("form_registro"):
        nombre = st.text_input("Nombre", key="reg_nombre")
        email = st.text_input("Correo", key="reg_email")
        password = st.text_input("Contraseña", type="password", key="reg_pass")
        enviado = st.form_submit_button("Crear cuenta", use_container_width=True)
    if enviado:
        if len(password or "") < 6:
            st.error("La contraseña debe tener al menos 6 caracteres.")
            return
        ok, msg = registrar(email, password, nombre)
        (st.success if ok else st.error)(msg)
