"""Cliente Supabase cacheado.

Provee acceso al cliente anónimo (flujo de usuario, respeta RLS) y, cuando se
requiere, al cliente con service-role (solo operaciones administrativas del
lado servidor). Las llaves viven exclusivamente en ``st.secrets``.
"""
from __future__ import annotations

import streamlit as st

try:
    from supabase import Client, create_client
except ImportError:  # pragma: no cover - supabase no instalado en algunos entornos
    Client = object  # type: ignore
    create_client = None  # type: ignore


def _secret(nombre: str, defecto=None):
    """Lee un secreto de forma tolerante (no revienta si falta el archivo)."""
    try:
        return st.secrets[nombre]
    except Exception:
        return defecto


def credenciales_configuradas() -> bool:
    """True si hay URL + anon key para conectarse a Supabase."""
    return bool(_secret("SUPABASE_URL")) and bool(_secret("SUPABASE_ANON_KEY"))


@st.cache_resource(show_spinner=False)
def get_client() -> "Client":
    """Cliente anónimo de Supabase (respeta RLS). Cacheado por proceso."""
    if create_client is None:
        raise RuntimeError("El paquete 'supabase' no está instalado.")
    url = _secret("SUPABASE_URL")
    key = _secret("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError(
            "Faltan SUPABASE_URL / SUPABASE_ANON_KEY en st.secrets."
        )
    return create_client(url, key)


@st.cache_resource(show_spinner=False)
def get_service_client() -> "Client":
    """Cliente con service-role. Solo para tareas administrativas server-side.

    Nunca debe usarse en el flujo normal de usuario ni exponerse al cliente.
    """
    if create_client is None:
        raise RuntimeError("El paquete 'supabase' no está instalado.")
    url = _secret("SUPABASE_URL")
    key = _secret("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError(
            "Faltan SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY en st.secrets."
        )
    return create_client(url, key)


def demo_habilitado() -> bool:
    """El modo demo está disponible si se habilita en secrets o si no hay BD."""
    valor = _secret("DEMO_MODE_ENABLED", None)
    if valor is None:
        # Sin credenciales, el demo es el único modo posible.
        return not credenciales_configuradas()
    return bool(valor)


def dominios_permitidos() -> list[str]:
    dominios = _secret("ALLOWED_EMAIL_DOMAINS", []) or []
    if isinstance(dominios, str):
        dominios = [dominios]
    return [str(d).strip().lower() for d in dominios if str(d).strip()]
