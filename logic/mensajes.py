"""Clasificación de mensajes (SMS / Reminder) por estatus de entrega."""
from __future__ import annotations

import pandas as pd

# Palabras que denotan entrega/éxito en la columna 'descripcion'.
PALABRAS_EXITO = [
    "entregado", "enviado", "exitoso", "exito", "delivered", "ok",
    "recibido", "sent", "success",
]
PALABRAS_FALLO = [
    "no entregado", "fallido", "falla", "error", "rebotado", "rechazado",
    "no exitoso", "failed", "undelivered", "bounce", "invalido", "invalid",
]


def es_exitoso(descripcion) -> str:
    """Devuelve 'Exitoso' o 'No exitoso' según la descripción del mensaje."""
    t = str(descripcion or "").strip().lower()
    if not t:
        return "No exitoso"
    for palabra in PALABRAS_FALLO:
        if palabra in t:
            return "No exitoso"
    for palabra in PALABRAS_EXITO:
        if palabra in t:
            return "Exitoso"
    return "No exitoso"


def resumen_mensajes(df: pd.DataFrame) -> dict:
    """KPIs de un archivo de mensajes (SMS o Reminder)."""
    if df is None or df.empty or "descripcion" not in df.columns:
        return {"total": 0, "exitosos": 0, "no_exitosos": 0, "pct_exito": 0.0}
    total = len(df)
    clases = df["descripcion"].apply(es_exitoso)
    exitosos = int((clases == "Exitoso").sum())
    no_exitosos = total - exitosos
    pct = round(100 * exitosos / total, 1) if total else 0.0
    return {
        "total": total,
        "exitosos": exitosos,
        "no_exitosos": no_exitosos,
        "pct_exito": pct,
    }
