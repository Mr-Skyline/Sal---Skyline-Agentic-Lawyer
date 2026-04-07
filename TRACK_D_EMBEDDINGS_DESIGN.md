# Track D — Embeddings & pattern search (design only)

**Status:** Design note. **No production vectors, embedding API calls, or search UI** until product and counsel explicitly approve scope, vendor, and data classes.

---

## Goal

Enable **semantic / similarity search** across matter-adjacent text (e.g. past threads, review exports, optional internal notes) without changing Sal’s core JSON contract. This doc bounds options; it does not commit the repo to a stack.

---

## Candidate data sources

| Source | Contents | Sensitivity |
|--------|----------|-------------|
| Gmail threads (archived by `sync_worker`) | Subjects, bodies, headers | High (client / third-party PII) |
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
| Embedding job CLI or worker | New module (e.g. `embed_jobs.py`) or extension of `sync_worker` **only if** decoupled and feature-flagged |
| Vector store | Supabase `pgvector` (same project as metadata) **or** external hosted vector DB — decision TBD |
| Config | New env vars in `.env.example` only after approval (e.g. model id, dimensions, batch size) |
| UI | Streamlit search panel — **Agent 1–2** domain once APIs exist |

**Today:** `db.py` and `supabase_schema.sql` are **metadata-only**; no vector columns are assumed.

---

## Privacy & boundaries

- **No legal conclusions in embedding pipelines:** Classifiers or tags derived from embeddings must not be presented as “deadline” or “outcome” advice; they are search aids only.
- **Minimize retention of vectors:** If vectors are dropped when matters close, document that in the written retention policy (counsel-owned checklist in `docs/SKYLINE_BUILD_REVIEW.md`).
- **Third-party APIs:** If embeddings run outside the firm’s Supabase/tenant, record **what text leaves the boundary**, logging redaction options, and whether zero-retention / BAA-style terms apply (business/legal, not coded here).

---

## Open decisions (for Agents 1–2 + product)

1. Which **sources** ship in v1 (threads only vs include `skyline_review`)?
2. **pgvector vs external** vector store vs “embed on read” prototype?
3. **Access control:** Same service role as today, or per-matter RLS if vectors land in Supabase?
4. Sal integration: **retrieve-then-augment** Grok context vs standalone search UI only?

---

## References

- Phase table: `docs/SKYLINE_BUILD_REVIEW.md`
- Metadata schema: `supabase_schema.sql`
- Ops: `docs/OPERATIONS_ELITE.txt`, `verify_setup.py --supabase-ping`
