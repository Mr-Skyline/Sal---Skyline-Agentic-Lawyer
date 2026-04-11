"""
Track D — Embeddings pipeline for semantic search.

Feature-flagged: set EMBEDDINGS_ENABLED=1 in .env to activate.
Uses Supabase Edge Function with built-in gte-small model (384 dimensions, no external API key needed).

  python embed_jobs.py embed --source threads    # embed archived Gmail threads
  python embed_jobs.py embed --source reviews    # embed skyline_review/*.md
  python embed_jobs.py search "payment dispute Colorado"
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import sitepath

sitepath.ensure()

import requests
from dotenv import load_dotenv

from sal.config import ROOT, SKYLINE_REVIEW_DIR

load_dotenv(ROOT / ".env", override=True)

EMBEDDINGS_ENABLED = os.environ.get("EMBEDDINGS_ENABLED", "").strip().lower() in (
    "1",
    "true",
    "yes",
)
EMBED_DIMENSIONS = 384
EMBED_BATCH_SIZE = int(os.environ.get("EMBED_BATCH_SIZE", "5"))
CORRESPONDENCE_ARCHIVE_DIR = os.environ.get("CORRESPONDENCE_ARCHIVE_DIR", "").strip()


def _require_enabled() -> None:
    if not EMBEDDINGS_ENABLED:
        print(
            "Embeddings are disabled. Set EMBEDDINGS_ENABLED=1 in .env to activate.",
            file=sys.stderr,
        )
        sys.exit(1)


def _supabase_url() -> str:
    url = os.environ.get("SUPABASE_URL", "").strip()
    if not url:
        raise ValueError("Set SUPABASE_URL in .env")
    return url


def _supabase_key() -> str:
    key = (
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.environ.get("SUPABASE_KEY", "").strip()
    )
    if not key:
        raise ValueError("Set SUPABASE_SERVICE_ROLE_KEY in .env")
    return key


def _get_supabase():
    from supabase import create_client

    return create_client(_supabase_url(), _supabase_key())


def chunk_text(text: str, max_tokens: int = 512, overlap: int = 64) -> List[str]:
    """Split text into chunks by approximate token count (4 chars ~ 1 token)."""
    chars_per_token = 4
    max_chars = max_tokens * chars_per_token
    overlap_chars = overlap * chars_per_token

    if len(text) <= max_chars:
        return [text] if text else []

    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap_chars
    return chunks


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Generate embeddings via Supabase Edge Function (gte-small, 384 dimensions)."""
    url = f"{_supabase_url()}/functions/v1/embed"
    key = _supabase_key()
    results = []

    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i : i + EMBED_BATCH_SIZE]
        try:
            resp = requests.post(
                url,
                json={"input": batch},
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            results.extend(data["embeddings"])
        except Exception:
            for text in batch:
                resp = requests.post(
                    url,
                    json={"input": text},
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json",
                    },
                    timeout=60,
                )
                resp.raise_for_status()
                data = resp.json()
                results.extend(data["embeddings"])

    return results


def load_thread_chunks(archive_dir: str) -> List[Dict[str, Any]]:
    """Load archived Gmail threads and chunk them."""
    chunks = []
    p = Path(archive_dir)
    if not p.is_dir():
        print(f"Archive dir not found: {archive_dir}", file=sys.stderr)
        return chunks

    for f in sorted(p.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        thread_id = f.stem
        messages = data if isinstance(data, list) else data.get("messages", [data])
        subject = ""
        if messages and isinstance(messages[0], dict):
            subject = messages[0].get("subject", "")

        for msg_idx, msg in enumerate(messages):
            if not isinstance(msg, dict):
                continue
            body = (msg.get("text") or msg.get("body") or "").strip()
            if not body:
                continue
            prefix = f"Subject: {subject}\n\n" if subject else ""
            text_chunks = chunk_text(prefix + body)
            for idx, chunk in enumerate(text_chunks):
                chunks.append(
                    {
                        "source_type": "thread",
                        "source_id": thread_id,
                        "chunk_index": msg_idx * 100 + idx,
                        "content": chunk,
                        "metadata": {
                            "subject": subject,
                            "file": f.name,
                            "msg_index": msg_idx,
                        },
                    }
                )
    return chunks


def load_review_chunks(review_dir: Path) -> List[Dict[str, Any]]:
    """Load skyline_review Markdown files and chunk by section."""
    chunks = []
    if not review_dir.is_dir():
        return chunks

    for md in sorted(review_dir.rglob("*.md")):
        try:
            text = md.read_text(encoding="utf-8")
        except OSError:
            continue

        rel = str(md.relative_to(review_dir))
        sections = text.split("\n## ")
        for idx, section in enumerate(sections):
            section = section.strip()
            if not section:
                continue
            if idx > 0:
                section = "## " + section
            text_chunks = chunk_text(section)
            for cidx, chunk in enumerate(text_chunks):
                chunk_idx = idx * 100 + cidx
                chunks.append(
                    {
                        "source_type": "review",
                        "source_id": rel,
                        "chunk_index": chunk_idx,
                        "content": chunk,
                        "metadata": {"file": rel, "section_index": idx},
                    }
                )
    return chunks


def upsert_embeddings(
    supabase_client, chunks: List[Dict[str, Any]], embeddings: List[List[float]]
) -> int:
    """Upsert chunk + embedding pairs into document_embeddings."""
    inserted = 0
    for chunk, emb in zip(chunks, embeddings):
        row = {
            "source_type": chunk["source_type"],
            "source_id": chunk["source_id"],
            "chunk_index": chunk["chunk_index"],
            "content": chunk["content"],
            "metadata": json.dumps(chunk.get("metadata", {})),
            "embedding": emb,
        }
        try:
            supabase_client.table("document_embeddings").upsert(
                row, on_conflict="source_type,source_id,chunk_index"
            ).execute()
            inserted += 1
        except Exception as e:
            print(f"  skip {chunk['source_type']}/{chunk['source_id']}#{chunk['chunk_index']}: {e}")
    return inserted


def search_similar(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Semantic search across embedded documents."""
    sb = _get_supabase()
    query_embedding = embed_texts([query])[0]

    result = sb.rpc(
        "match_documents",
        {
            "query_embedding": query_embedding,
            "match_threshold": 0.5,
            "match_count": top_k,
        },
    ).execute()

    return result.data if result.data else []


def cmd_embed(args) -> int:
    """Embed threads or reviews."""
    _require_enabled()
    sb = _get_supabase()

    if args.source == "threads":
        if not CORRESPONDENCE_ARCHIVE_DIR:
            print("Set CORRESPONDENCE_ARCHIVE_DIR in .env", file=sys.stderr)
            return 1
        chunks = load_thread_chunks(CORRESPONDENCE_ARCHIVE_DIR)
    elif args.source == "reviews":
        chunks = load_review_chunks(SKYLINE_REVIEW_DIR)
    else:
        print(f"Unknown source: {args.source}", file=sys.stderr)
        return 1

    if not chunks:
        print(f"No chunks found for source={args.source}")
        return 0

    print(f"Embedding {len(chunks)} chunks from {args.source}...")
    texts = [c["content"] for c in chunks]
    embeddings = embed_texts(texts)
    inserted = upsert_embeddings(sb, chunks, embeddings)
    print(f"Done: {inserted}/{len(chunks)} upserted.")
    return 0


def cmd_search(args) -> int:
    """Search embedded documents."""
    _require_enabled()
    results = search_similar(args.query, top_k=args.top_k)
    if not results:
        print("No results.")
        return 0
    for i, r in enumerate(results, 1):
        sim = r.get("similarity", 0)
        src = r.get("source_type", "?")
        sid = r.get("source_id", "?")
        content = r.get("content", "")[:200]
        print(f"{i}. [{src}/{sid}] (sim={sim:.3f})")
        print(f"   {content}...")
        print()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Track D — Embeddings pipeline")
    sub = parser.add_subparsers(dest="command")

    embed_p = sub.add_parser("embed", help="Embed threads or reviews")
    embed_p.add_argument("--source", required=True, choices=["threads", "reviews"])

    search_p = sub.add_parser("search", help="Semantic search")
    search_p.add_argument("query", help="Search query")
    search_p.add_argument("--top-k", type=int, default=5, help="Number of results")

    args = parser.parse_args()
    if args.command == "embed":
        return cmd_embed(args)
    elif args.command == "search":
        return cmd_search(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
