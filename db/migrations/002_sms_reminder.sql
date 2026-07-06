-- =========================================================
-- Migración 002: tablas SMS y Reminder
-- Ejecutar en el SQL Editor de Supabase si ya corriste schema.sql antes.
-- =========================================================

create table if not exists public.sms (
  id                bigint generated always as identity primary key,
  carga_id          uuid not null references public.cargas(id) on delete cascade,
  codigo_de_cliente text,
  descripcion       text
);

create table if not exists public.reminder (
  id                bigint generated always as identity primary key,
  carga_id          uuid not null references public.cargas(id) on delete cascade,
  codigo_de_cliente text,
  descripcion       text
);

alter table public.sms      enable row level security;
alter table public.reminder enable row level security;

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
