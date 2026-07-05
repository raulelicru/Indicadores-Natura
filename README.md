# Dashboard Ejecutivo de Cobranza Natura

Aplicación web ejecutiva de cobranza (Streamlit + Supabase) que centraliza los
KPIs del mes de cierre para reuniones de seguimiento. Incluye login con
Supabase Auth, persistencia en Postgres con RLS, modo demostración con datos
sintéticos y 9 pestañas de análisis.

## Stack

- Python 3.11+, Streamlit (`layout="wide"`)
- Supabase Auth + Postgres con Row Level Security
- `supabase-py` (v2), Pandas, NumPy, OpenPyXL
- Plotly Express / Graph Objects

## Estructura

```
dashboard.py          # entry-point: router de auth + render de tabs
auth/                 # session.py (login/refresh/logout), roles.py (gating)
db/                   # client.py, schema.sql, writers.py, readers.py
ingest/               # loaders.py (xlsx/xls/csv), normalizers.py
logic/                # temporalidad, contactabilidad, promesas
ui/                   # login_view, welcome_view, admin_view, tabs/tab1..tab9
demo/                 # synthetic.py (datos sintéticos, seed 2025)
```

## Configuración local

1. Crea el entorno e instala dependencias:

   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Copia `.streamlit/secrets.toml.example` a `.streamlit/secrets.toml` y
   completa tus valores de Supabase:

   ```toml
   SUPABASE_URL = "https://<proyecto>.supabase.co"
   SUPABASE_ANON_KEY = "<anon-key>"
   SUPABASE_SERVICE_ROLE_KEY = "<service-role-key>"   # solo admin server-side
   ALLOWED_EMAIL_DOMAINS = ["tudominio.com"]
   DEMO_MODE_ENABLED = true
   ```

   > `secrets.toml` está en `.gitignore`; nunca se commitea. La
   > `SERVICE_ROLE_KEY` solo se usa server-side para tareas administrativas.

3. Ejecuta el esquema `db/schema.sql` en el SQL editor de Supabase (crea
   tablas, funciones, políticas RLS y el trigger de creación de perfiles).

4. Arranca la app:

   ```bash
   streamlit run dashboard.py
   ```

## Modos de uso

- **Demostración**: sin credenciales de Supabase (o con
  `DEMO_MODE_ENABLED = true`), la app genera datos sintéticos y **no** escribe
  en la base de datos.
- **Real**: autenticado, un usuario `admin`/`ejecutivo` carga archivos
  (Cartera, Pagos, Gestión, Promesas). Los datos se normalizan, se registran en
  `cargas` y se guardan por lotes en sus tablas. Al recargar, se reconstruyen
  desde Postgres.

## Roles

- `admin`: carga archivos, ve todo y administra usuarios.
- `ejecutivo`: carga y ve su cartera.
- `consulta`: solo lectura de dashboards (rol por defecto al registrarse).

El aislamiento entre usuarios lo garantiza RLS (no solo la UI).

## Despliegue

Streamlit Community Cloud, entry-point `dashboard.py`. Configura las mismas
claves de `secrets.toml` en el panel de Secrets de la app.
