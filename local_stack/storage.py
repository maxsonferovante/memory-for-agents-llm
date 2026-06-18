from __future__ import annotations

import json
import os
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import psycopg2
from psycopg2.extras import RealDictCursor


VECTOR_DIMENSIONS = 48


SCHEMA = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS ingest_events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    repo TEXT NOT NULL,
    branch TEXT,
    commit_sha TEXT,
    file_path TEXT,
    scope TEXT,
    document_id TEXT,
    revision_id TEXT,
    parent_revision_id TEXT,
    operation TEXT,
    canonical_path TEXT,
    source TEXT,
    session_id TEXT,
    created_at TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    raw_payload_path TEXT NOT NULL,
    raw_markdown_path TEXT,
    content TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    processed_at TEXT,
    error TEXT
);

CREATE TABLE IF NOT EXISTS job_queue (
    id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL REFERENCES ingest_events(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    next_run_at TEXT NOT NULL,
    last_error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memory_items (
    id TEXT PRIMARY KEY,
    event_id TEXT UNIQUE REFERENCES ingest_events(id) ON DELETE CASCADE,
    repo TEXT NOT NULL,
    scope TEXT NOT NULL,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    source_file TEXT NOT NULL,
    commit_sha TEXT,
    content_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    supersedes_id TEXT,
    provenance_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memory_chunks (
    id TEXT PRIMARY KEY,
    memory_item_id TEXT NOT NULL REFERENCES memory_items(id) ON DELETE CASCADE,
    repo TEXT NOT NULL,
    scope TEXT NOT NULL,
    kind TEXT NOT NULL,
    heading_path TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(48),
    token_count INTEGER NOT NULL,
    source_file TEXT NOT NULL,
    provenance_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS document_revisions (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    event_id TEXT UNIQUE NOT NULL REFERENCES ingest_events(id) ON DELETE CASCADE,
    repo TEXT NOT NULL,
    scope TEXT NOT NULL,
    canonical_path TEXT NOT NULL,
    source_file TEXT NOT NULL,
    operation TEXT NOT NULL,
    parent_revision_id TEXT,
    title TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    frontmatter_json TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    body_text TEXT NOT NULL,
    links_json TEXT NOT NULL,
    references_json TEXT NOT NULL,
    provenance_json TEXT NOT NULL,
    status TEXT NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS document_sections (
    id TEXT PRIMARY KEY,
    revision_id TEXT NOT NULL REFERENCES document_revisions(id) ON DELETE CASCADE,
    document_id TEXT NOT NULL,
    section_index INTEGER NOT NULL,
    level INTEGER NOT NULL,
    heading TEXT,
    heading_path TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    blocks_json TEXT NOT NULL,
    links_json TEXT NOT NULL,
    references_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS consolidation_snapshots (
    id TEXT PRIMARY KEY,
    scope TEXT NOT NULL,
    repo TEXT NOT NULL DEFAULT '',
    slug TEXT NOT NULL,
    title TEXT NOT NULL,
    document_ids_json TEXT NOT NULL,
    snapshot_json TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(scope, repo, slug)
);

CREATE TABLE IF NOT EXISTS reconciliation_conflicts (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    repo TEXT NOT NULL,
    canonical_path TEXT NOT NULL,
    database_revision_id TEXT,
    repo_content_hash TEXT,
    status TEXT NOT NULL,
    details_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS writeback_suggestions (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    target_path TEXT NOT NULL,
    based_on_revision_id TEXT NOT NULL REFERENCES document_revisions(id) ON DELETE CASCADE,
    suggestion_json TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

ALTER TABLE ingest_events ADD COLUMN IF NOT EXISTS document_id TEXT;
ALTER TABLE ingest_events ADD COLUMN IF NOT EXISTS revision_id TEXT;
ALTER TABLE ingest_events ADD COLUMN IF NOT EXISTS parent_revision_id TEXT;
ALTER TABLE ingest_events ADD COLUMN IF NOT EXISTS operation TEXT;
ALTER TABLE ingest_events ADD COLUMN IF NOT EXISTS canonical_path TEXT;

ALTER TABLE memory_chunks ADD COLUMN IF NOT EXISTS embedding vector(48);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'memory_chunks' AND column_name = 'embedding_json'
    ) THEN
        UPDATE memory_chunks
        SET embedding = CAST(embedding_json AS vector(48))
        WHERE embedding IS NULL AND embedding_json IS NOT NULL;
    END IF;
END
$$;

ALTER TABLE memory_chunks ALTER COLUMN embedding SET NOT NULL;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'memory_chunks' AND column_name = 'embedding_json'
    ) THEN
        ALTER TABLE memory_chunks DROP COLUMN embedding_json;
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS idx_job_queue_status_next_run ON job_queue(status, next_run_at);
CREATE INDEX IF NOT EXISTS idx_memory_items_repo_scope ON memory_items(repo, scope);
CREATE INDEX IF NOT EXISTS idx_memory_chunks_item ON memory_chunks(memory_item_id);
CREATE INDEX IF NOT EXISTS idx_ingest_events_document_id ON ingest_events(document_id, created_at);
CREATE INDEX IF NOT EXISTS idx_document_revisions_document ON document_revisions(document_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_document_sections_revision ON document_sections(revision_id, section_index);
CREATE INDEX IF NOT EXISTS idx_consolidation_snapshots_scope_slug ON consolidation_snapshots(scope, repo, slug);
CREATE INDEX IF NOT EXISTS idx_reconciliation_conflicts_document ON reconciliation_conflicts(document_id, status);
CREATE INDEX IF NOT EXISTS idx_writeback_suggestions_document ON writeback_suggestions(document_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_chunks_embedding_cosine
ON memory_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
"""


@dataclass(frozen=True)
class IngestedEvent:
    id: str
    event_type: str
    repo: str
    branch: str | None
    commit_sha: str | None
    file_path: str | None
    scope: str
    document_id: str | None
    revision_id: str | None
    parent_revision_id: str | None
    operation: str | None
    canonical_path: str | None
    source: str | None
    session_id: str | None
    created_at: str
    content_hash: str
    raw_payload_path: str
    raw_markdown_path: str | None
    content: str | None
    status: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def connect(db_path: Path | None = None):
    database_url = os.environ.get("MEMORY_DATABASE_URL")
    if not database_url:
        raise RuntimeError("MEMORY_DATABASE_URL is required")
    conn = psycopg2.connect(database_url)
    conn.autocommit = False
    return conn


def initialize(conn) -> None:
    with conn.cursor() as cursor:
        cursor.execute(SCHEMA)
    conn.commit()


@contextmanager
def transaction(conn) -> Iterator[object]:
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    else:
        conn.commit()


def execute(conn, sql: str, params: tuple[object, ...] = ()) -> None:
    with conn.cursor() as cursor:
        cursor.execute(sql, params)


def fetchone(conn, sql: str, params: tuple[object, ...] = ()) -> dict[str, object] | None:
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(sql, params)
        row = cursor.fetchone()
        return dict(row) if row is not None else None


def fetchall(conn, sql: str, params: tuple[object, ...] = ()) -> list[dict[str, object]]:
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.17g}" for value in values) + "]"


def save_event(
    conn,
    *,
    event_id: str,
    payload: dict[str, object],
    raw_payload_path: Path,
    raw_markdown_path: Path | None,
    content: str | None,
    content_hash: str,
) -> None:
    with transaction(conn):
        execute(
            conn,
            """
            INSERT INTO ingest_events (
                id, event_type, repo, branch, commit_sha, file_path, scope, document_id,
                revision_id, parent_revision_id, operation, canonical_path, source,
                session_id, created_at, content_hash, raw_payload_path, raw_markdown_path,
                content, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
            """,
            (
                event_id,
                str(payload.get("event_type", "session_stop")),
                str(payload.get("repo", "unknown")),
                payload.get("branch"),
                payload.get("commit_sha"),
                payload.get("file_path"),
                str(payload.get("scope", "repo")),
                payload.get("document_id"),
                payload.get("revision_id"),
                payload.get("parent_revision_id"),
                payload.get("operation"),
                payload.get("canonical_path"),
                payload.get("source"),
                payload.get("session_id"),
                str(payload.get("created_at", utc_now())),
                content_hash,
                str(raw_payload_path),
                str(raw_markdown_path) if raw_markdown_path else None,
                content,
            ),
        )
        now = utc_now()
        execute(
            conn,
            """
            INSERT INTO job_queue (id, event_id, status, attempts, next_run_at, created_at, updated_at)
            VALUES (%s, %s, 'pending', 0, %s, %s, %s)
            """,
            (event_id, event_id, now, now, now),
        )


def claim_next_job(conn) -> dict[str, object] | None:
    now = utc_now()
    with transaction(conn):
        row = fetchone(
            conn,
            """
            SELECT * FROM job_queue
            WHERE status = 'pending' AND next_run_at <= %s
            ORDER BY created_at
            FOR UPDATE SKIP LOCKED
            LIMIT 1
            """,
            (now,),
        )
        if row is None:
            return None
        execute(
            conn,
            """
            UPDATE job_queue
            SET status = 'processing', attempts = attempts + 1, updated_at = %s
            WHERE id = %s
            """,
            (now, row["id"]),
        )
        event = fetchone(conn, "SELECT * FROM ingest_events WHERE id = %s", (row["event_id"],))
    return event


def mark_job_complete(conn, event_id: str) -> None:
    now = utc_now()
    with transaction(conn):
        execute(conn, "UPDATE job_queue SET status = 'done', updated_at = %s WHERE id = %s", (now, event_id))
        execute(
            conn,
            "UPDATE ingest_events SET status = 'processed', processed_at = %s, error = NULL WHERE id = %s",
            (now, event_id),
        )


def mark_job_failed(conn, event_id: str, error: str) -> None:
    now = utc_now()
    with transaction(conn):
        execute(
            conn,
            """
            UPDATE job_queue
            SET status = 'failed', last_error = %s, updated_at = %s
            WHERE id = %s
            """,
            (error[:1000], now, event_id),
        )
        execute(
            conn,
            "UPDATE ingest_events SET status = 'failed', processed_at = %s, error = %s WHERE id = %s",
            (now, error[:1000], event_id),
        )


def upsert_memory_item(conn, record: dict[str, object]) -> None:
    with transaction(conn):
        execute(
            conn,
            """
            INSERT INTO memory_items (
                id, event_id, repo, scope, kind, title, summary, source_file, commit_sha,
                content_hash, status, supersedes_id, provenance_json, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                summary = excluded.summary,
                updated_at = excluded.updated_at,
                status = excluded.status
            """,
            (
                record["id"],
                record["event_id"],
                record["repo"],
                record["scope"],
                record["kind"],
                record["title"],
                record["summary"],
                record["source_file"],
                record.get("commit_sha"),
                record["content_hash"],
                record["status"],
                record.get("supersedes_id"),
                json.dumps(record["provenance"], ensure_ascii=False, sort_keys=True),
                record["created_at"],
                record["updated_at"],
            ),
        )


def replace_chunks(conn, memory_item_id: str, chunks: list[dict[str, object]]) -> None:
    with transaction(conn):
        execute(conn, "DELETE FROM memory_chunks WHERE memory_item_id = %s", (memory_item_id,))
        for chunk in chunks:
            execute(
                conn,
                """
                INSERT INTO memory_chunks (
                    id, memory_item_id, repo, scope, kind, heading_path, chunk_index,
                    chunk_text, embedding, token_count, source_file, provenance_json, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CAST(%s AS vector(48)), %s, %s, %s, %s)
                """,
                (
                    chunk["id"],
                    memory_item_id,
                    chunk["repo"],
                    chunk["scope"],
                    chunk["kind"],
                    chunk["heading_path"],
                    chunk["chunk_index"],
                    chunk["chunk_text"],
                    vector_literal(list(chunk["embedding"])),
                    chunk["token_count"],
                    chunk["source_file"],
                    json.dumps(chunk["provenance"], ensure_ascii=False, sort_keys=True),
                    chunk["created_at"],
                ),
            )


def fetch_latest_document_revision(
    conn, document_id: str
) -> dict[str, object] | None:
    return fetchone(
        conn,
        """
        SELECT *
        FROM document_revisions
        WHERE document_id = %s
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (document_id,),
    )


def upsert_document_revision(conn, record: dict[str, object]) -> None:
    with transaction(conn):
        if record["status"] in {"active", "deleted"}:
            execute(
                conn,
                """
                UPDATE document_revisions
                SET status = 'superseded', updated_at = %s
                WHERE document_id = %s AND id <> %s AND status = 'active'
                """,
                (record["updated_at"], record["document_id"], record["id"]),
            )
        execute(
            conn,
            """
            INSERT INTO document_revisions (
                id, document_id, event_id, repo, scope, canonical_path, source_file,
                operation, parent_revision_id, title, content_hash, frontmatter_json,
                raw_text, body_text, links_json, references_json, provenance_json,
                status, is_deleted, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT(id) DO UPDATE SET
                canonical_path = excluded.canonical_path,
                source_file = excluded.source_file,
                operation = excluded.operation,
                parent_revision_id = excluded.parent_revision_id,
                title = excluded.title,
                content_hash = excluded.content_hash,
                frontmatter_json = excluded.frontmatter_json,
                raw_text = excluded.raw_text,
                body_text = excluded.body_text,
                links_json = excluded.links_json,
                references_json = excluded.references_json,
                provenance_json = excluded.provenance_json,
                status = excluded.status,
                is_deleted = excluded.is_deleted,
                updated_at = excluded.updated_at
            """,
            (
                record["id"],
                record["document_id"],
                record["event_id"],
                record["repo"],
                record["scope"],
                record["canonical_path"],
                record["source_file"],
                record["operation"],
                record.get("parent_revision_id"),
                record["title"],
                record["content_hash"],
                json.dumps(record["frontmatter"], ensure_ascii=False, sort_keys=True),
                record["raw_text"],
                record["body_text"],
                json.dumps(record["links"], ensure_ascii=False),
                json.dumps(record["references"], ensure_ascii=False),
                json.dumps(record["provenance"], ensure_ascii=False, sort_keys=True),
                record["status"],
                bool(record.get("is_deleted", False)),
                record["created_at"],
                record["updated_at"],
            ),
        )


def replace_document_sections(
    conn, revision_id: str, sections: list[dict[str, object]]
) -> None:
    with transaction(conn):
        execute(conn, "DELETE FROM document_sections WHERE revision_id = %s", (revision_id,))
        for section in sections:
            execute(
                conn,
                """
                INSERT INTO document_sections (
                    id, revision_id, document_id, section_index, level, heading, heading_path,
                    raw_text, blocks_json, links_json, references_json, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    section["id"],
                    revision_id,
                    section["document_id"],
                    section["section_index"],
                    section["level"],
                    section.get("heading"),
                    section["heading_path"],
                    section["raw_text"],
                    json.dumps(section["blocks"], ensure_ascii=False),
                    json.dumps(section["links"], ensure_ascii=False),
                    json.dumps(section["references"], ensure_ascii=False),
                    section["created_at"],
                ),
            )


def upsert_consolidation_snapshot(conn, record: dict[str, object]) -> None:
    with transaction(conn):
        execute(
            conn,
            """
            INSERT INTO consolidation_snapshots (
                id, scope, repo, slug, title, document_ids_json, snapshot_json,
                content_hash, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT(scope, repo, slug) DO UPDATE SET
                id = excluded.id,
                title = excluded.title,
                document_ids_json = excluded.document_ids_json,
                snapshot_json = excluded.snapshot_json,
                content_hash = excluded.content_hash,
                updated_at = excluded.updated_at
            """,
            (
                record["id"],
                record["scope"],
                record.get("repo", ""),
                record["slug"],
                record["title"],
                json.dumps(record["document_ids"], ensure_ascii=False),
                json.dumps(record["snapshot"], ensure_ascii=False),
                record["content_hash"],
                record["created_at"],
                record["updated_at"],
            ),
        )


def clear_reconciliation_conflicts(conn, document_id: str) -> None:
    with transaction(conn):
        execute(
            conn,
            "DELETE FROM reconciliation_conflicts WHERE document_id = %s",
            (document_id,),
        )


def upsert_reconciliation_conflict(conn, record: dict[str, object]) -> None:
    with transaction(conn):
        execute(
            conn,
            """
            INSERT INTO reconciliation_conflicts (
                id, document_id, repo, canonical_path, database_revision_id, repo_content_hash,
                status, details_json, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT(id) DO UPDATE SET
                database_revision_id = excluded.database_revision_id,
                repo_content_hash = excluded.repo_content_hash,
                status = excluded.status,
                details_json = excluded.details_json,
                updated_at = excluded.updated_at
            """,
            (
                record["id"],
                record["document_id"],
                record["repo"],
                record["canonical_path"],
                record.get("database_revision_id"),
                record.get("repo_content_hash"),
                record["status"],
                json.dumps(record["details"], ensure_ascii=False),
                record["created_at"],
                record["updated_at"],
            ),
        )


def upsert_writeback_suggestion(conn, record: dict[str, object]) -> None:
    with transaction(conn):
        execute(
            conn,
            """
            INSERT INTO writeback_suggestions (
                id, document_id, target_path, based_on_revision_id, suggestion_json, status,
                created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT(id) DO UPDATE SET
                suggestion_json = excluded.suggestion_json,
                status = excluded.status,
                updated_at = excluded.updated_at
            """,
            (
                record["id"],
                record["document_id"],
                record["target_path"],
                record["based_on_revision_id"],
                json.dumps(record["suggestion"], ensure_ascii=False),
                record["status"],
                record["created_at"],
                record["updated_at"],
            ),
        )
