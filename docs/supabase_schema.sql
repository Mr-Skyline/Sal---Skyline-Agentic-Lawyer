-- Schema version: 1.1.0
-- Last updated: 2026-04-09
-- Apply: Supabase Dashboard → SQL → New query → paste → Run
--
-- Skyline / sync_worker + Streamlit audit metadata
--
-- HOW TO APPLY (ops)
--   1) Confirm header version (this file is 1.1.0); Supabase Dashboard → SQL → New query → paste this file → Run.
--   2) Use service role key only in server-side .env (sync_worker / worker); never in browsers.
--   3) pip install -r requirements-supabase.txt in the project venv.
--   4) python -m src.sal.verify_setup --supabase-ping  (must print "supabase-ping: ok" when URL+key set).

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

-- Auto-update updated_at on row modification
create or replace function public.update_updated_at_column()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

create trigger correspondence_threads_updated_at
    before update on public.correspondence_threads
    for each row
    execute function public.update_updated_at_column();

-- Row-Level Security (enable when exposing tables to client-side / anon key)
-- Currently: service role bypasses RLS. Enable these before any browser-facing Supabase calls.

-- alter table public.correspondence_threads enable row level security;
-- alter table public.skyline_review_exports enable row level security;

-- Service role: full access (already implicit, but explicit for documentation)
-- create policy "Service role full access on threads"
--   on public.correspondence_threads
--   for all
--   using (auth.role() = 'service_role');

-- create policy "Service role full access on exports"
--   on public.skyline_review_exports
--   for all
--   using (auth.role() = 'service_role');

-- Authenticated users: read-only (uncomment when adding client-side queries)
-- create policy "Authenticated read on threads"
--   on public.correspondence_threads
--   for select
--   using (auth.role() = 'authenticated');

-- create policy "Authenticated read on exports"
--   on public.skyline_review_exports
--   for select
--   using (auth.role() = 'authenticated');

-- v1.1 migration candidate: add updated_at to review exports (for future append-tracking)
-- alter table public.skyline_review_exports add column if not exists updated_at timestamptz default now();
-- create index if not exists skyline_review_exports_updated_at_idx
--   on public.skyline_review_exports (updated_at desc);

-- --------------------------------------------------------------------------
-- Track D: Semantic search (pgvector)
-- Enable the extension first: Supabase Dashboard → Database → Extensions → vector → Enable
-- Or: create extension if not exists vector;
-- --------------------------------------------------------------------------

create table if not exists public.sal_embeddings (
  id bigint generated always as identity primary key,
  content_hash text not null,
  source_type text not null default 'gmail_thread',
  source_id text,
  source_path text,
  chunk_text text not null,
  metadata jsonb default '{}',
  embedding vector(1536),
  created_at timestamptz not null default now(),
  unique (content_hash)
);

create index if not exists sal_embeddings_source_idx
  on public.sal_embeddings (source_type, source_id);

-- IVFFlat index for cosine similarity. Requires some rows to exist for optimal
-- clustering; harmless on empty/small tables but won't speed up queries until
-- the table has a few hundred rows.
create index if not exists sal_embeddings_embedding_idx
  on public.sal_embeddings
  using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

comment on table public.sal_embeddings is 'Track D: text chunks with vector embeddings for semantic search (pgvector)';

-- Similarity search RPC for Track D
create or replace function public.match_sal_embeddings(
  query_embedding vector(1536),
  match_count int default 10,
  match_threshold float default 0.0,
  filter_source_type text default null
)
returns table (
  id bigint,
  chunk_text text,
  source_type text,
  source_id text,
  source_path text,
  metadata jsonb,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    se.id,
    se.chunk_text,
    se.source_type,
    se.source_id,
    se.source_path,
    se.metadata,
    1 - (se.embedding <=> query_embedding) as similarity
  from public.sal_embeddings se
  where
    (filter_source_type is null or se.source_type = filter_source_type)
    and 1 - (se.embedding <=> query_embedding) > match_threshold
  order by se.embedding <=> query_embedding
  limit match_count;
end;
$$;
