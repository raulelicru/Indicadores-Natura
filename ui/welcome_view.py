"""Bienvenida + carga de archivos (modo real) y disparo del modo demo."""
from __future__ import annotations

import streamlit as st

from auth.roles import puede_cargar, rol_actual
from ingest.loaders import leer_tabla
from ingest.normalizers import normalizar

# Tipos de archivo que se pueden cargar y persistir.
TIPOS = {
    "cartera": "Cartera / Remesa",
    "pagos": "Pagos",
    "gestion": "Gestión (Vici)",
    "promesas": "Promesas",
    "sms": "Resultados SMS",
    "reminder": "Reminder",
    "inicios": "Cuentas establecidas e Inicios",
}


def render_welcome(user_id: str, periodo: str) -> dict | None:
    """Pantalla de carga. Devuelve un dataset normalizado si el usuario procesa.

    Devuelve ``None`` si aún no hay nada procesado.
    """
    st.subheader("📁 Carga de archivos del cierre")
    st.caption(
        f"Periodo seleccionado: **{periodo}** · Rol: **{rol_actual()}**"
    )

    if not puede_cargar():
        st.warning(
            "Tu rol es de solo consulta. No puedes cargar archivos; "
            "visualiza los datos ya cargados en las pestañas."
        )
        return None

    datos: dict = {"periodo": periodo, "modo": "real"}
    nombres: dict = {}
    cols = st.columns(2)
    for i, (tipo, etiqueta) in enumerate(TIPOS.items()):
        with cols[i % 2]:
            archivo = st.file_uploader(
                etiqueta,
                type=["xlsx", "xls", "csv"],
                key=f"upl_{tipo}",
            )
            if archivo is not None:
                try:
                    crudo = leer_tabla(archivo.getvalue(), archivo.name)
                    df = normalizar(tipo, crudo)
                    datos[tipo] = df
                    nombres[tipo] = archivo.name
                    st.success(f"{etiqueta}: {len(df):,} filas leídas.")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"No se pudo leer {etiqueta}: {exc}")

    st.session_state["nombres_archivos"] = nombres

    hay_datos = any(k in datos for k in TIPOS)
    if not hay_datos:
        st.info("Sube al menos un archivo para procesar el cierre.")
        return None

    if st.button("✅ Procesar y visualizar", type="primary"):
        return datos
    return None
