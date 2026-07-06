"""Reconstrucción de DataFrames desde Postgres (respetando RLS)."""
from __future__ import annotations

import pandas as pd

from auth.session import cliente_autenticado

_PAGE = 1000


def _select_todo(client, tabla: str, carga_ids: list[str]) -> pd.DataFrame:
    """Trae todas las filas de una tabla para un conjunto de cargas (paginado)."""
    if not carga_ids:
        return pd.DataFrame()
    filas: list[dict] = []
    desde = 0
    while True:
        resp = (
            client.table(tabla)
            .select("*")
            .in_("carga_id", carga_ids)
            .range(desde, desde + _PAGE - 1)
            .execute()
        )
        lote = resp.data or []
        filas.extend(lote)
        if len(lote) < _PAGE:
            break
        desde += _PAGE
    return pd.DataFrame(filas)


def ultima_carga_por_tipo(user_id: str, periodo: str) -> dict:
    """Devuelve {tipo_archivo: carga_id} de la última carga por tipo/periodo."""
    client = cliente_autenticado()
    resp = (
        client.table("cargas")
        .select("id, tipo_archivo, cargado_en")
        .eq("periodo", periodo)
        .order("cargado_en", desc=True)
        .execute()
    )
    ultimas: dict[str, str] = {}
    for fila in resp.data or []:
        tipo = fila.get("tipo_archivo")
        if tipo and tipo not in ultimas:
            ultimas[tipo] = fila.get("id")
    return ultimas


def periodos_disponibles(user_id: str) -> list[str]:
    """Lista de periodos con cargas para el usuario (o todos si admin)."""
    client = cliente_autenticado()
    try:
        resp = (
            client.table("cargas")
            .select("periodo")
            .order("periodo", desc=True)
            .execute()
        )
        vistos = []
        for fila in resp.data or []:
            p = fila.get("periodo")
            if p and p not in vistos:
                vistos.append(p)
        return vistos
    except Exception:  # noqa: BLE001
        return []


def cargar_dataset(user_id: str, periodo: str) -> dict:
    """Reconstruye el paquete de DataFrames para un periodo desde Postgres."""
    client = cliente_autenticado()
    ultimas = ultima_carga_por_tipo(user_id, periodo)

    def _tabla(tipo: str) -> pd.DataFrame:
        carga_id = ultimas.get(tipo)
        if not carga_id:
            return pd.DataFrame()
        df = _select_todo(client, tipo, [carga_id])
        # Normaliza tipos numéricos/fecha tras venir de JSON.
        return _coerce(tipo, df)

    return {
        "periodo": periodo,
        "modo": "real",
        "cartera": _tabla("cartera"),
        "pagos": _tabla("pagos"),
        "gestion": _tabla("gestion"),
        "promesas": _tabla("promesas"),
        "sms": _tabla("sms"),
        "reminder": _tabla("reminder"),
        "comparativo": cargar_comparativo(user_id),
    }


def _coerce(tipo: str, df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    numericas = {
        "cartera": ["aging_de_morosidad", "valor_saldo_deuda"],
        "pagos": ["pago"],
        "gestion": ["duracion_seg"],
        "promesas": ["monto_promesa"],
    }.get(tipo, [])
    fechas = {
        "pagos": ["fecha_pago"],
        "promesas": ["fecha_promesa"],
    }.get(tipo, [])
    for col in numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in fechas:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def cargar_comparativo(user_id: str) -> pd.DataFrame:
    """Histórico de KPIs de cierre (para la pestaña Comparativo)."""
    client = cliente_autenticado()
    try:
        resp = (
            client.table("kpis_cierre")
            .select("periodo, recuperacion, meta, cumplimiento_pct")
            .order("periodo", desc=False)
            .execute()
        )
        filas = resp.data or []
        if not filas:
            return pd.DataFrame(
                columns=["periodo", "segmento", "recuperacion", "meta",
                         "cumplimiento_pct"]
            )
        df = pd.DataFrame(filas)
        df["segmento"] = "Total"
        return df
    except Exception:  # noqa: BLE001
        return pd.DataFrame(
            columns=["periodo", "segmento", "recuperacion", "meta",
                     "cumplimiento_pct"]
        )
