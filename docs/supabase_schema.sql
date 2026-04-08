-- Skyline / sync_worker + Streamlit audit metadata
--
-- HOW TO APPLY (ops)
--   1) Supabase Dashboard → SQL → New query → paste this file → Run.
--   2) Use service role key only in server-side .env (sync_worker / worker); never in browsers.
--   3) pip install -r requirements-supabase.txt in the project venv.
--   4) python -m src.sal.verify_setup --supabase-ping  (must print "supabase-ping: ok" when URL+key set).
--
-- RLS: not defined here. For server-only service role, table access bypasses RLS by default.
--    If you expose Supabase to clients later, enable RLS and add policies.

create table if not exists public.correspondence_threads (
  id bigint generated always as identity primary key,
  gmail_thread_id text not null unique,
  subject text,
  last_message_internal_date bigint,
  archive_path text,
  updated_at timestamptz not null default now()
);

create index if not exists correspondence_threads_updated_at_idx
  on public.correspondence_threads (updated_at desc);

comment on table public.correspondence_threads is 'Gmail thread snapshots ingested by sync_worker.py';

-- Optional audit index for Streamlit -> skyline_review/*.md exports (metadata only; no claim bodies).
create table if not exists public.skyline_review_exports (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  primary_state text,
  state_subdir text not null,
  file_name text not null
);

create index if not exists skyline_review_exports_created_at_idx
  on public.skyline_review_exports (created_at desc);

comment on table public.skyline_review_exports is 'Sal-style review Markdown writes from review_export.export_analysis_markdown (filename + folder only)';
