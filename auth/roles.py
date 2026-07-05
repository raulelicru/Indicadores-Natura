"""Lectura de perfil/rol y helpers de gating de UI por permiso."""
from __future__ import annotations

import functools

import streamlit as st

from auth.session import cliente_autenticado

ROLES = ("admin", "ejecutivo", "consulta")
ROL_DEFECTO = "consulta"


def cargar_perfil(forzar: bool = False) -> dict:
    """Carga el perfil del usuario actual desde 'perfiles' (cacheado en sesión)."""
    if not forzar and st.session_state.get("perfil"):
        return st.session_state["perfil"]

    user_id = st.session_state.get("user_id")
    perfil = {
        "id": user_id,
        "nombre": st.session_state.get("user_email"),
        "rol": ROL_DEFECTO,
        "zona_asignada": None,
    }
    if user_id:
        try:
            client = cliente_autenticado()
            resp = (
                client.table("perfiles")
                .select("*")
                .eq("id", user_id)
                .limit(1)
                .execute()
            )
            filas = resp.data or []
            if filas:
                perfil.update(filas[0])
        except Exception:  # noqa: BLE001 - si falla, queda rol por defecto
            pass
    st.session_state["perfil"] = perfil
    return perfil


def rol_actual() -> str:
    return (st.session_state.get("perfil") or cargar_perfil()).get(
        "rol", ROL_DEFECTO
    )


def es_admin() -> bool:
    return rol_actual() == "admin"


def es_ejecutivo() -> bool:
    return rol_actual() == "ejecutivo"


def es_consulta() -> bool:
    return rol_actual() == "consulta"


def puede_cargar() -> bool:
    """admin y ejecutivo cargan archivos; consulta no."""
    return rol_actual() in ("admin", "ejecutivo")


def puede_administrar_usuarios() -> bool:
    return es_admin()


def requiere_rol(*roles_permitidos: str):
    """Decorador: ejecuta la función solo si el rol actual está permitido."""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if rol_actual() in roles_permitidos:
                return fn(*args, **kwargs)
            st.warning("No tienes permisos para esta acción.")
            return None
        return wrapper
    return deco
