"""Administración de usuarios (solo rol admin)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from auth.roles import ROLES, puede_administrar_usuarios
from auth.session import cliente_autenticado


def render_admin() -> None:
    if not puede_administrar_usuarios():
        st.warning("Solo un administrador puede acceder a esta sección.")
        return

    st.subheader("👥 Administración de usuarios")
    st.caption("Gestiona roles y zonas asignadas. Las escrituras respetan RLS.")

    try:
        client = cliente_autenticado()
        resp = client.table("perfiles").select("*").order("creado_en").execute()
        filas = resp.data or []
    except Exception as exc:  # noqa: BLE001
        st.error(f"No se pudieron leer los perfiles: {exc}")
        return

    if not filas:
        st.info("No hay perfiles registrados todavía.")
        return

    df = pd.DataFrame(filas)
    st.dataframe(df[["nombre", "rol", "zona_asignada"]],
                 use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("#### Cambiar rol de un usuario")
    opciones = {f"{f.get('nombre') or f['id']} ({f['id'][:8]})": f["id"]
                for f in filas}
    with st.form("form_rol"):
        etiqueta = st.selectbox("Usuario", list(opciones.keys()))
        nuevo_rol = st.selectbox("Nuevo rol", ROLES)
        zona = st.text_input("Zona asignada (opcional)")
        enviado = st.form_submit_button("Actualizar", type="primary")
    if enviado:
        user_id = opciones[etiqueta]
        try:
            payload = {"rol": nuevo_rol}
            if zona.strip():
                payload["zona_asignada"] = zona.strip()
            client.table("perfiles").update(payload).eq("id", user_id).execute()
            st.success("Rol actualizado.")
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            st.error(f"No se pudo actualizar: {exc}")
