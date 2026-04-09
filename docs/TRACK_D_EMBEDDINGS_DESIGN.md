# Track D — Embeddings & pattern search (design only)

**Status:** v1 implemented. Chunking engine (`src/sal/embeddings.py`), pgvector store (`src/sal/vector_store.py`), Streamlit search panel, schema v1.1. Gmail thread archives are the v1 source. Review Markdown indexing and RAG augmentation are deferred to v2.

---

## Goal

Enable **semantic / similarity search** across matter-adjacent text (e.g. past threads, review exports, optional internal notes) without changing Sal’s core JSON contract. This doc bounds options; it does not commit the repo to a stack.

---

## Candidate data sources

| Source | Contents | Sensitivity |
|--------|----------|-------------|
| Gmail threads (archived by `src/sal/sync_worker`) | Subjects, bodies, headers | High (client / third-party PII) |
| `skyline_review/*.md` | Sal analysis + intake + evidence excerpt | High |
| Supabase `correspondence_threads` | Metadata today (subject, ids, paths) — **not** full bodies unless schema extended | Lower if bodies stay off-DB |
| OCR outputs (optional) | Image-derived text from evidence | High |

**Rule:** Anything that can identify individuals or privileged content follows the same handling as the rest of Skyline: **internal tool**, no implied consent to ship raw text to a vendor without a deliberate decision, DPAs, and env isolation.

---

## Chunking (proposed)

- **Unit of embed:** Prefer **one chunk per logical message** or **per ~512–1k token window** with small overlap if a single message is long. Subject line can be prefixed to each chunk for retrieval context.
- **Thread boundaries:** Do not merge unrelated threads; carry `gmail_thread_id` (or file path) as metadata on every vector row.
- **Review Markdown:** Section-aware splits (e.g. by `##`) with front-matter / matter id in metadata.
- **De-duplication:** Skip near-duplicate chunks from repeated footers or quoted threads (hash or simhash — implementation detail).

Final chunk sizes depend on the chosen embedding model’s context limit and cost.

---

## Where it could live in the repo (future)

| Piece | Likely location / pattern |
|-------|---------------------------|
| Embedding job CLI or worker | New module under `src/sal/` (e.g. `embed_jobs.py`) or extension of `src/sal/sync_worker` **only if** decoupled and feature-flagged |
| Vector store | Supabase `pgvector` (same project as metadata) **or** external hosted vector DB — decision TBD |
| Config | New env vars in `.env.example` only after approval (e.g. model id, dimensions, batch size) |
| UI | Streamlit search panel — **Agent 1–2** domain once APIs exist |

**Today:** `src/sal/db.py` and `docs/supabase_schema.sql` are **metadata-only**; no vector columns are assumed.

---

## Privacy & boundaries

- **No legal conclusions in embedding pipelines:** Classifiers or tags derived from embeddings must not be presented as “deadline” or “outcome” advice; they are search aids only.
- **Minimize retention of vectors:** If vectors are dropped when matters close, document that in the written retention policy (counsel-owned checklist in `docs/SKYLINE_BUILD_REVIEW.md`).
- **Third-party APIs:** If embeddings run outside the firm’s Supabase/tenant, record **what text leaves the boundary**, logging redaction options, and whether zero-retention / BAA-style terms apply (business/legal, not coded here).

---

## Open decisions (for Agents 1–2 + product)

1. Which **sources** ship in v1 (threads only vs include `skyline_review`)? → **Decided:** v1 sources are **Gmail thread archives** only. `skyline_review/*.md` indexing deferred to v2.
2. **pgvector vs external** vector store vs “embed on read” prototype? → **Decided:** **pgvector in Supabase** (same project as metadata). `sal_embeddings` table + `match_sal_embeddings` RPC in `docs/supabase_schema.sql` v1.1.
3. **Access control:** Same service role as today, or per-matter RLS if vectors land in Supabase? → **Decided:** Same **service role** as today. Per-matter RLS deferred until browser-facing exposure is considered.
4. Sal integration: **retrieve-then-augment** Grok context vs standalone search UI only? → **Decided:** **Standalone search UI** in Streamlit (experimental expander). RAG augmentation of Grok context deferred to v2.

---

## References

- Phase table: `docs/SKYLINE_BUILD_REVIEW.md`
- Metadata schema: `docs/supabase_schema.sql`
- Ops: `docs/OPERATIONS_ELITE.txt`, `python -m src.sal.verify_setup --supabase-ping`
