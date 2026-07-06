"""Datos sintéticos para el modo demostración (seed 2025).

No toca la base de datos. Devuelve DataFrames con el mismo esquema canónico
que produce la ingesta real, de modo que las pestañas funcionan igual en ambos
modos.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from logic.temporalidad import ORDEN_TEMPORALIDAD, pac_temporalidad

SEED = 2025

ZONAS = ["Norte", "Sur", "Centro", "Occidente", "Oriente"]
SEGMENTOS = ["Diamante", "Oro", "Plata", "Bronce", "Nuevo"]
CAMINOS = ["Inicio", "Crecimiento", "Establecida", "Reactivada"]
CANALES = ["Llamada", "SMS", "WhatsApp", "Email"]
ASESORES = [f"Asesor {n}" for n in range(1, 11)]
ESTATUS_PROMESA = ["Vigente", "Cumplida", "Caída"]


def _rng() -> np.random.RandomState:
    return np.random.RandomState(SEED)


def generar_cartera(n: int = 1200) -> pd.DataFrame:
    r = _rng()
    codigos = [f"C{100000 + i}" for i in range(n)]
    aging = r.choice(
        np.arange(1, 240),
        size=n,
        p=_pesos_aging(),
    )
    saldo = np.round(r.gamma(2.2, 480, size=n) + 60, 2)
    df = pd.DataFrame({
        "codigo_de_cliente": codigos,
        "aging_de_morosidad": aging.astype(int),
        "valor_saldo_deuda": saldo,
        "segmentacion_rep": r.choice(SEGMENTOS, size=n, p=[.12, .20, .28, .28, .12]),
        "rango_edad_consultora": r.choice(CAMINOS, size=n),
        "zona": r.choice(ZONAS, size=n),
        "estado": r.choice(["Activo", "Suspendido", "En gestión"], size=n,
                           p=[.55, .15, .30]),
    })
    df["temporalidad"] = df["aging_de_morosidad"].apply(pac_temporalidad)
    return df


def _pesos_aging() -> np.ndarray:
    # Más peso en aging bajo (mora temprana) decayendo hacia mora tardía.
    x = np.arange(1, 240)
    pesos = np.exp(-x / 70.0)
    return pesos / pesos.sum()


def generar_pagos(cartera: pd.DataFrame, tasa: float = 0.42) -> pd.DataFrame:
    r = _rng()
    n_pagos = int(len(cartera) * tasa)
    clientes = cartera.sample(n=n_pagos, random_state=SEED, replace=False)
    # Un pago parcial o total del saldo.
    fraccion = r.uniform(0.25, 1.05, size=n_pagos)
    pago = np.round(clientes["valor_saldo_deuda"].values * fraccion, 2)
    dias = r.randint(1, 29, size=n_pagos)
    fechas = pd.to_datetime("2025-06-01") + pd.to_timedelta(dias, unit="D")
    df = pd.DataFrame({
        "codigo_de_cliente": clientes["codigo_de_cliente"].values,
        "pago": pago,
        "fecha_pago": fechas,
        "asesor": r.choice(ASESORES, size=n_pagos),
        "temporalidad": clientes["temporalidad"].values,
    })
    return df


def generar_gestion(cartera: pd.DataFrame, intentos_por_cliente: float = 2.3) -> pd.DataFrame:
    r = _rng()
    n = int(len(cartera) * intentos_por_cliente)
    clientes = cartera.sample(n=n, random_state=SEED + 1, replace=True)
    disposiciones_contacto = [
        "Contacto titular - promesa de pago",
        "Contacto efectivo - acuerdo",
        "Titular atiende - compromiso",
    ]
    disposiciones_no = [
        "No contesta", "Buzón de voz", "Número equivocado",
        "Ocupado", "Sin respuesta",
    ]
    es_contacto = r.rand(n) < 0.38
    list_desc = np.where(
        es_contacto,
        r.choice(disposiciones_contacto, size=n),
        r.choice(disposiciones_no, size=n),
    )
    contactabilidad = np.where(es_contacto, "Contacto", "No contacto")
    horas = r.randint(8, 20, size=n)
    df = pd.DataFrame({
        "codigo_de_cliente": clientes["codigo_de_cliente"].values,
        "list_description": list_desc,
        "contactabilidad": contactabilidad,
        "hora_llamada": [f"{h:02d}:00" for h in horas],
        "canal": r.choice(CANALES, size=n, p=[.55, .2, .18, .07]),
        "asesor": r.choice(ASESORES, size=n),
        "duracion_seg": np.where(
            es_contacto, r.randint(40, 400, size=n), r.randint(0, 25, size=n)
        ),
    })
    return df


def generar_promesas(gestion: pd.DataFrame, cartera: pd.DataFrame) -> pd.DataFrame:
    r = _rng()
    con_promesa = gestion[gestion["contactabilidad"] == "Contacto"]
    con_promesa = con_promesa.drop_duplicates("codigo_de_cliente")
    n = len(con_promesa)
    saldo_map = cartera.set_index("codigo_de_cliente")["valor_saldo_deuda"]
    montos = con_promesa["codigo_de_cliente"].map(saldo_map).fillna(300.0).values
    montos = np.round(montos * r.uniform(0.4, 1.0, size=n), 2)
    dias = r.randint(1, 25, size=n)
    fechas = pd.to_datetime("2025-06-05") + pd.to_timedelta(dias, unit="D")
    df = pd.DataFrame({
        "codigo_de_cliente": con_promesa["codigo_de_cliente"].values,
        "monto_promesa": montos,
        "fecha_promesa": fechas,
        "estatus": r.choice(ESTATUS_PROMESA, size=n, p=[.30, .48, .22]),
    })
    return df


def generar_sms(cartera: pd.DataFrame) -> pd.DataFrame:
    r = _rng()
    n = int(len(cartera) * 0.8)
    clientes = cartera.sample(n=n, random_state=SEED + 2, replace=True)
    descripcion = r.choice(
        ["Entregado", "No entregado", "Fallido", "Enviado"],
        size=n, p=[.62, .18, .10, .10],
    )
    return pd.DataFrame({
        "codigo_de_cliente": clientes["codigo_de_cliente"].values,
        "descripcion": descripcion,
    })


def generar_reminder(cartera: pd.DataFrame) -> pd.DataFrame:
    r = _rng()
    n = int(len(cartera) * 0.6)
    clientes = cartera.sample(n=n, random_state=SEED + 3, replace=True)
    descripcion = r.choice(
        ["Exitoso", "No exitoso", "Entregado", "Rebotado"],
        size=n, p=[.55, .20, .15, .10],
    )
    return pd.DataFrame({
        "codigo_de_cliente": clientes["codigo_de_cliente"].values,
        "descripcion": descripcion,
    })


def generar_inicios(cartera: pd.DataFrame) -> pd.DataFrame:
    r = _rng()
    clientes = cartera[["codigo_de_cliente"]].drop_duplicates().copy()
    n = len(clientes)
    clientes["estatus"] = r.choice(["Establecida", "Inicio"], size=n, p=[.69, .31])
    clientes["tipo_pedido"] = r.choice(
        ["PROPIO", "LIDER", "CALL CENTER"], size=n, p=[.71, .27, .02])
    return clientes.reset_index(drop=True)


def generar_comparativo() -> pd.DataFrame:
    """Histórico mensual de recuperación por segmento (para tab Comparativo)."""
    r = _rng()
    meses = pd.date_range("2025-01-01", "2025-06-01", freq="MS")
    filas = []
    base = {"Diamante": 92000, "Oro": 70000, "Plata": 51000,
            "Bronce": 33000, "Nuevo": 18000}
    for i, mes in enumerate(meses):
        for seg, val in base.items():
            recuperado = val * (1 + 0.03 * i) * r.uniform(0.85, 1.12)
            meta = val * (1 + 0.03 * i) * 1.05
            filas.append({
                "periodo": mes.strftime("%Y-%m"),
                "segmento": seg,
                "recuperacion": round(recuperado, 2),
                "meta": round(meta, 2),
                "cumplimiento_pct": round(100 * recuperado / meta, 1),
            })
    return pd.DataFrame(filas)


def generar_dataset(periodo: str = "2025-06") -> dict:
    """Genera el paquete completo de DataFrames para el modo demo."""
    cartera = generar_cartera()
    pagos = generar_pagos(cartera)
    gestion = generar_gestion(cartera)
    promesas = generar_promesas(gestion, cartera)
    comparativo = generar_comparativo()
    sms = generar_sms(cartera)
    reminder = generar_reminder(cartera)
    inicios = generar_inicios(cartera)
    return {
        "periodo": periodo,
        "modo": "demo",
        "cartera": cartera,
        "pagos": pagos,
        "gestion": gestion,
        "promesas": promesas,
        "sms": sms,
        "reminder": reminder,
        "inicios": inicios,
        "comparativo": comparativo,
    }
