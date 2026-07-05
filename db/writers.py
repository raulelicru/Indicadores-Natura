"""Persistencia en Postgres: registra cargas y hace upsert por lotes.

Toda escritura pasa por el cliente autenticado del usuario, por lo que RLS se
aplica automáticamente (una fila solo se inserta si su carga pertenece al
usuario o si es admin).
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from auth.session import cliente_autenticado

CHUNK = 500

# Columnas destino por tabla (deben existir en el esquema).
COLUMNAS = {
    "cartera": [
        "codigo_de_cliente", "aging_de_morosidad", "valor_saldo_deuda",
        "segmentacion_rep", "rango_edad_consultora", "zona", "estado",
        "temporalidad",
    ],
    "pagos": [
        "codigo_de_cliente", "pago", "fecha_pago", "asesor", "temporalidad",
    ],
    "gestion": [
        "codigo_de_cliente", "list_description", "contactabilidad",
        "hora_llamada", "canal", "asesor", "duracion_seg",
    ],
    "promesas": [
        "codigo_de_cliente", "monto_promesa", "fecha_promesa", "estatus",
    ],
}


def _limpiar_valor(v):
    """Convierte valores a tipos serializables por el cliente Supabase."""
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if isinstance(v, (np.floating,)):
        return None if np.isnan(v) else float(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (pd.Timestamp,)):
        if pd.isna(v):
            return None
        return v.date().isoformat()
    if pd.isna(v) if np.isscalar(v) else False:
        return None
    return v


def _df_a_registros(df: pd.DataFrame, columnas: list[str], carga_id: str) -> list[dict]:
    registros = []
    for _, fila in df.iterrows():
        reg = {"carga_id": carga_id}
        for col in columnas:
            reg[col] = _limpiar_valor(fila.get(col))
        registros.append(reg)
    return registros


def crear_carga(user_id: str, tipo_archivo: str, nombre_archivo: str,
                periodo: str, filas: int) -> str | None:
    """Inserta una fila en 'cargas' y devuelve su id."""
    client = cliente_autenticado()
    resp = (
        client.table("cargas")
        .insert({
            "user_id": user_id,
            "tipo_archivo": tipo_archivo,
            "nombre_archivo": nombre_archivo,
            "periodo": periodo,
            "filas": int(filas),
        })
        .execute()
    )
    filas_resp = resp.data or []
    if filas_resp:
        return filas_resp[0].get("id")
    return None


def guardar_tabla(tipo_archivo: str, df: pd.DataFrame, carga_id: str) -> int:
    """Inserta por lotes (chunks de ~500) las filas de un DataFrame."""
    if df is None or df.empty:
        return 0
    columnas = COLUMNAS.get(tipo_archivo)
    if columnas is None:
        raise ValueError(f"Tipo de archivo no soportado: {tipo_archivo}")
    client = cliente_autenticado()
    registros = _df_a_registros(df, columnas, carga_id)
    total = 0
    for i in range(0, len(registros), CHUNK):
        lote = registros[i:i + CHUNK]
        client.table(tipo_archivo).insert(lote).execute()
        total += len(lote)
    return total


def persistir_dataset(user_id: str, periodo: str, datos: dict,
                      nombres: dict | None = None) -> dict:
    """Crea una carga por cada tabla presente y persiste sus filas.

    ``datos`` es un dict {tipo_archivo: DataFrame}. Devuelve un resumen
    {tipo_archivo: filas_guardadas}.
    """
    nombres = nombres or {}
    resumen: dict[str, int] = {}
    for tipo in ("cartera", "pagos", "gestion", "promesas"):
        df = datos.get(tipo)
        if df is None or df.empty:
            continue
        carga_id = crear_carga(
            user_id=user_id,
            tipo_archivo=tipo,
            nombre_archivo=nombres.get(tipo, f"{tipo}.xlsx"),
            periodo=periodo,
            filas=len(df),
        )
        if not carga_id:
            continue
        resumen[tipo] = guardar_tabla(tipo, df, carga_id)
    return resumen


def guardar_kpis_cierre(user_id: str, periodo: str, kpis: dict) -> None:
    """Guarda un snapshot de KPIs de cierre para el histórico/comparativo."""
    client = cliente_autenticado()
    payload = {
        "user_id": user_id,
        "periodo": periodo,
        "recuperacion": kpis.get("recuperacion"),
        "meta": kpis.get("meta"),
        "cumplimiento_pct": kpis.get("cumplimiento_pct"),
        "contact_rate": kpis.get("contact_rate"),
        "promesas_generadas": kpis.get("promesas_generadas"),
        "promesas_caidas": kpis.get("promesas_caidas"),
        "json_detalle": kpis.get("json_detalle"),
    }
    client.table("kpis_cierre").insert(payload).execute()
