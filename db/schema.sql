-- =========================================================
-- Dashboard Ejecutivo de Cobranza Natura
-- DDL + políticas RLS. Ejecutar en el SQL editor de Supabase.
-- =========================================================

-- =========================================================
-- PERFILES (1:1 con auth.users)
-- =========================================================
create table if not exists public.perfiles (
  id            uuid primary key references auth.users(id) on delete cascade,
  nombre        text,
  rol           text not null default 'consulta'
                  check (rol in ('admin','ejecutivo','consulta')),
  zona_asignada text,
  creado_en     timestamptz not null default now()
);

-- =========================================================
-- CARGAS (auditoría de cada ingesta de archivos)
-- =========================================================
create table if not exists public.cargas (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null references auth.users(id) on delete cascade,
  tipo_archivo  text not null,   -- cartera | pagos | gestion | promesas | comparativo | ...
  nombre_archivo text,
  periodo       text not null,   -- p.ej. '2026-06'
  filas         integer,
  cargado_en    timestamptz not null default now()
);

-- =========================================================
-- CARTERA / REMESA
-- =========================================================
create table if not exists public.cartera (
  id                   bigint generated always as identity primary key,
  carga_id             uuid not null references public.cargas(id) on delete cascade,
  codigo_de_cliente    text,
  aging_de_morosidad   integer,
  valor_saldo_deuda    numeric,
  segmentacion_rep     text,
  rango_edad_consultora text,
  zona                 text,
  estado               text,
  temporalidad         text     -- T1..T7 (derivada)
);

-- =========================================================
-- PAGOS
-- =========================================================
create table if not exists public.pagos (
  id                bigint generated always as identity primary key,
  carga_id          uuid not null references public.cargas(id) on delete cascade,
  codigo_de_cliente text,
  pago              numeric,
  fecha_pago        date,
  asesor            text,
  temporalidad      text
);

-- =========================================================
-- GESTION (Vici)
-- =========================================================
create table if not exists public.gestion (
  id                bigint generated always as identity primary key,
  carga_id          uuid not null references public.cargas(id) on delete cascade,
  codigo_de_cliente text,
  list_description  text,
  contactabilidad   text,
  hora_llamada      text,
  canal             text,
  asesor            text,
  duracion_seg      integer
);

-- =========================================================
-- PROMESAS
-- =========================================================
create table if not exists public.promesas (
  id                bigint generated always as identity primary key,
  carga_id          uuid not null references public.cargas(id) on delete cascade,
  codigo_de_cliente text,
  monto_promesa     numeric,
  fecha_promesa     date,
  estatus           text
);

-- =========================================================
-- KPIS_CIERRE (snapshot por periodo para histórico/comparativo)
-- =========================================================
create table if not exists public.kpis_cierre (
  id                  bigint generated always as identity primary key,
  user_id             uuid not null references auth.users(id) on delete cascade,
  periodo             text not null,
  recuperacion        numeric,
  meta                numeric,
  cumplimiento_pct    numeric,
  contact_rate        numeric,
  promesas_generadas  integer,
  promesas_caidas     integer,
  json_detalle        jsonb,
  generado_en         timestamptz not null default now()
);

-- =========================================================
-- ROW LEVEL SECURITY
-- =========================================================
alter table public.perfiles    enable row level security;
alter table public.cargas      enable row level security;
alter table public.cartera     enable row level security;
alter table public.pagos       enable row level security;
alter table public.gestion     enable row level security;
alter table public.promesas    enable row level security;
alter table public.kpis_cierre enable row level security;

-- Helper: ¿el usuario actual es admin?
create or replace function public.es_admin()
returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.perfiles p
                 where p.id = auth.uid() and p.rol = 'admin');
$$;

-- PERFILES: cada quien lee su perfil; admin lee todos; solo admin cambia roles
drop policy if exists perfiles_select_own on public.perfiles;
create policy perfiles_select_own on public.perfiles
  for select using (id = auth.uid() or public.es_admin());

drop policy if exists perfiles_update_admin on public.perfiles;
create policy perfiles_update_admin on public.perfiles
  for update using (public.es_admin());

drop policy if exists perfiles_insert_self on public.perfiles;
create policy perfiles_insert_self on public.perfiles
  for insert with check (id = auth.uid());

-- CARGAS: dueño o admin
drop policy if exists cargas_rw on public.cargas;
create policy cargas_rw on public.cargas
  for all using (user_id = auth.uid() or public.es_admin())
  with check (user_id = auth.uid() or public.es_admin());

-- Tablas de datos: acceso vía la carga a la que pertenecen
drop policy if exists cartera_rw on public.cartera;
create policy cartera_rw on public.cartera
  for all using (exists (select 1 from public.cargas c
     where c.id = carga_id and (c.user_id = auth.uid() or public.es_admin())))
  with check (exists (select 1 from public.cargas c
     where c.id = carga_id and (c.user_id = auth.uid() or public.es_admin())));

drop policy if exists pagos_rw on public.pagos;
create policy pagos_rw on public.pagos
  for all using (exists (select 1 from public.cargas c
     where c.id = carga_id and (c.user_id = auth.uid() or public.es_admin())))
  with check (exists (select 1 from public.cargas c
     where c.id = carga_id and (c.user_id = auth.uid() or public.es_admin())));

drop policy if exists gestion_rw on public.gestion;
create policy gestion_rw on public.gestion
  for all using (exists (select 1 from public.cargas c
     where c.id = carga_id and (c.user_id = auth.uid() or public.es_admin())))
  with check (exists (select 1 from public.cargas c
     where c.id = carga_id and (c.user_id = auth.uid() or public.es_admin())));

drop policy if exists promesas_rw on public.promesas;
create policy promesas_rw on public.promesas
  for all using (exists (select 1 from public.cargas c
     where c.id = carga_id and (c.user_id = auth.uid() or public.es_admin())))
  with check (exists (select 1 from public.cargas c
     where c.id = carga_id and (c.user_id = auth.uid() or public.es_admin())));

-- KPIS: dueño o admin
drop policy if exists kpis_rw on public.kpis_cierre;
create policy kpis_rw on public.kpis_cierre
  for all using (user_id = auth.uid() or public.es_admin())
  with check (user_id = auth.uid() or public.es_admin());

-- =========================================================
-- Trigger: al crear un usuario en auth.users, generar su perfil
-- con rol por defecto 'consulta'.
-- =========================================================
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.perfiles (id, nombre, rol)
  values (new.id, coalesce(new.raw_user_meta_data->>'nombre', new.email), 'consulta')
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- =========================================================
-- SMS (archivo "Resultados SMS") — col J = Descripcion
-- =========================================================
create table if not exists public.sms (
  id                bigint generated always as identity primary key,
  carga_id          uuid not null references public.cargas(id) on delete cascade,
  codigo_de_cliente text,
  descripcion       text
);

-- =========================================================
-- REMINDER (archivo "Reminder") — col J = Descripcion
-- =========================================================
create table if not exists public.reminder (
  id                bigint generated always as identity primary key,
  carga_id          uuid not null references public.cargas(id) on delete cascade,
  codigo_de_cliente text,
  descripcion       text
);

-- =========================================================
-- INICIOS (archivo "Cuentas establecidas e Inicios")
--   col C = INICIO/Estatus (Inicio | Establecida)
-- =========================================================
create table if not exists public.inicios (
  id                bigint generated always as identity primary key,
  carga_id          uuid not null references public.cargas(id) on delete cascade,
  codigo_de_cliente text,
  estatus           text,   -- Inicio | Establecida
  tipo_pedido       text    -- PROPIO | LIDER | CALL CENTER
);

alter table public.sms      enable row level security;
alter table public.reminder enable row level security;
alter table public.inicios  enable row level security;

drop policy if exists sms_rw on public.sms;
create policy sms_rw on public.sms
  for all using (exists (select 1 from public.cargas c
     where c.id = carga_id and (c.user_id = auth.uid() or public.es_admin())))
  with check (exists (select 1 from public.cargas c
     where c.id = carga_id and (c.user_id = auth.uid() or public.es_admin())));

drop policy if exists reminder_rw on public.reminder;
create policy reminder_rw on public.reminder
  for all using (exists (select 1 from public.cargas c
     where c.id = carga_id and (c.user_id = auth.uid() or public.es_admin())))
  with check (exists (select 1 from public.cargas c
     where c.id = carga_id and (c.user_id = auth.uid() or public.es_admin())));

drop policy if exists inicios_rw on public.inicios;
create policy inicios_rw on public.inicios
  for all using (exists (select 1 from public.cargas c
     where c.id = carga_id and (c.user_id = auth.uid() or public.es_admin())))
  with check (exists (select 1 from public.cargas c
     where c.id = carga_id and (c.user_id = auth.uid() or public.es_admin())));
