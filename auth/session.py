"""Gestión de sesión con Supabase Auth: login, registro, refresh, logout."""
from __future__ import annotations

import time

import streamlit as st

from db.client import dominios_permitidos, get_client

# Margen (segundos) antes de la expiración para refrescar el token.
_MARGEN_REFRESH = 120


def _guardar_sesion(session) -> None:
    """Persiste tokens de la sesión de Supabase en st.session_state."""
    if session is None:
        return
    st.session_state["access_token"] = getattr(session, "access_token", None)
    st.session_state["refresh_token"] = getattr(session, "refresh_token", None)
    st.session_state["expires_at"] = getattr(session, "expires_at", None)
    user = getattr(session, "user", None)
    if user is not None:
        st.session_state["user_id"] = getattr(user, "id", None)
        st.session_state["user_email"] = getattr(user, "email", None)


def sesion_valida() -> bool:
    """True si hay un access_token en sesión (se refresca por separado)."""
    return bool(st.session_state.get("access_token"))


def _dominio_permitido(email: str) -> bool:
    dominios = dominios_permitidos()
    if not dominios:
        return True  # sin restricción configurada
    email = (email or "").strip().lower()
    return any(email.endswith("@" + d) for d in dominios)


def iniciar_sesion(email: str, password: str) -> tuple[bool, str]:
    """Login con email/password. Devuelve (ok, mensaje)."""
    try:
        client = get_client()
        resp = client.auth.sign_in_with_password(
            {"email": email.strip(), "password": password}
        )
        if resp.session is None:
            return False, "Credenciales inválidas."
        _guardar_sesion(resp.session)
        return True, "Sesión iniciada."
    except Exception as exc:  # noqa: BLE001
        return False, f"No se pudo iniciar sesión: {_msg(exc)}"


def enviar_magic_link(email: str) -> tuple[bool, str]:
    """Envía un magic link (OTP por correo)."""
    email = email.strip()
    if not _dominio_permitido(email):
        return False, "Dominio de correo no permitido."
    try:
        client = get_client()
        client.auth.sign_in_with_otp({"email": email})
        return True, "Te enviamos un enlace de acceso a tu correo."
    except Exception as exc:  # noqa: BLE001
        return False, f"No se pudo enviar el enlace: {_msg(exc)}"


def registrar(email: str, password: str, nombre: str = "") -> tuple[bool, str]:
    """Registro restringido por dominio de correo permitido."""
    email = email.strip()
    if not _dominio_permitido(email):
        return False, "Dominio de correo no permitido para registro."
    try:
        client = get_client()
        resp = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"nombre": nombre or email}},
        })
        # Crea/asegura el perfil con rol por defecto 'consulta'.
        user = getattr(resp, "user", None)
        if user is not None and getattr(resp, "session", None) is not None:
            _guardar_sesion(resp.session)
            try:
                client.table("perfiles").upsert({
                    "id": user.id,
                    "nombre": nombre or email,
                    "rol": "consulta",
                }).execute()
            except Exception:  # noqa: BLE001 - lo cubre el trigger de la BD
                pass
        return True, (
            "Registro exitoso. Revisa tu correo si se requiere confirmación."
        )
    except Exception as exc:  # noqa: BLE001
        return False, f"No se pudo registrar: {_msg(exc)}"


def refrescar_si_necesario() -> None:
    """Refresca el token de forma transparente si está por expirar."""
    if not sesion_valida():
        return
    expires_at = st.session_state.get("expires_at")
    ahora = int(time.time())
    if expires_at and (int(expires_at) - ahora) > _MARGEN_REFRESH:
        return  # todavía válido
    refresh_token = st.session_state.get("refresh_token")
    if not refresh_token:
        return
    try:
        client = get_client()
        resp = client.auth.refresh_session(refresh_token)
        if getattr(resp, "session", None) is not None:
            _guardar_sesion(resp.session)
    except Exception:  # noqa: BLE001 - si falla, la próxima acción pedirá login
        pass


def cliente_autenticado():
    """Devuelve el cliente Supabase con la sesión del usuario aplicada."""
    client = get_client()
    access = st.session_state.get("access_token")
    refresh = st.session_state.get("refresh_token")
    if access and refresh:
        try:
            client.auth.set_session(access, refresh)
        except Exception:  # noqa: BLE001
            pass
    return client


def cerrar_sesion() -> None:
    """Logout: cierra en Supabase y limpia el estado local."""
    try:
        get_client().auth.sign_out()
    except Exception:  # noqa: BLE001
        pass
    st.session_state.clear()
    st.rerun()


def _msg(exc: Exception) -> str:
    """Mensaje de error limpio (sin exponer trazas ni llaves)."""
    texto = str(exc)
    if len(texto) > 200:
        texto = texto[:200] + "…"
    return texto
