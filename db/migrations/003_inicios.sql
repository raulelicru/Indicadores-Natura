-- =========================================================
-- Migración 003: tabla INICIOS (Cuentas establecidas e Inicios)
-- Ejecutar en el SQL Editor de Supabase si ya corriste schema.sql antes.
-- =========================================================

create table if not exists public.inicios (
  id                bigint generated always as identity primary key,
  carga_id          uuid not null references public.cargas(id) on delete cascade,
  codigo_de_cliente text,
  estatus           text,   -- Inicio | Establecida
  tipo_pedido       text    -- PROPIO | LIDER | CALL CENTER
);

alter table public.inicios enable row level security;

drop policy if exists inicios_rw on public.inicios;
create policy inicios_rw on public.inicios
  for all using (exists (select 1 from public.cargas c
     where c.id = carga_id and (c.user_id = auth.uid() or public.es_admin())))
  with check (exists (select 1 from public.cargas c
     where c.id = carga_id and (c.user_id = auth.uid() or public.es_admin())));
