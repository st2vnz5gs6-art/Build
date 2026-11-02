"""SQLite store: documents, clauses (with an FTS5 keyword index) and the audit log."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id      TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    revision    TEXT NOT NULL,
    filename    TEXT NOT NULL,
    sha256      TEXT NOT NULL,
    pages       INTEGER,
    tier        TEXT NOT NULL DEFAULT 'SPEN specification',
    synthetic   INTEGER NOT NULL DEFAULT 0,
    ingested_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS clauses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id      TEXT NOT NULL REFERENCES documents(doc_id) ON DELETE CASCADE,
    clause_no   TEXT NOT NULL,
    heading     TEXT NOT NULL,
    text        TEXT NOT NULL,
    page_start  INTEGER,
    page_end    INTEGER,
    parent_no   TEXT,
    path        TEXT NOT NULL DEFAULT '',
    ord         INTEGER NOT NULL,
    UNIQUE (doc_id, clause_no)
);
CREATE VIRTUAL TABLE IF NOT EXISTS clauses_fts USING fts5(
    doc_id UNINDEXED, clause_no, heading, path, text,
    content='clauses', content_rowid='id', tokenize="porter unicode61 tokenchars '/'"
);
CREATE TRIGGER IF NOT EXISTS clauses_ai AFTER INSERT ON clauses BEGIN
    INSERT INTO clauses_fts(rowid, doc_id, clause_no, heading, path, text)
    VALUES (new.id, new.doc_id, new.clause_no, new.heading, new.path, new.text);
END;
CREATE TRIGGER IF NOT EXISTS clauses_ad AFTER DELETE ON clauses BEGIN
    INSERT INTO clauses_fts(clauses_fts, rowid, doc_id, clause_no, heading, path, text)
    VALUES ('delete', old.id, old.doc_id, old.clause_no, old.heading, old.path, old.text);
END;
CREATE TABLE IF NOT EXISTS query_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT NOT NULL,
    mode        TEXT NOT NULL,
    query       TEXT NOT NULL,
    answer_json TEXT NOT NULL,
    cited       TEXT NOT NULL,
    rejected    TEXT NOT NULL DEFAULT '[]',
    model       TEXT NOT NULL
);
"""


@dataclass
class ClauseRow:
    id: int
    doc_id: str
    clause_no: str
    heading: str
    text: str
    page_start: int | None
    page_end: int | None
    parent_no: str | None
    path: str
    revision: str = ""
    title: str = ""
    tier: str = ""
    synthetic: bool = False

    @property
    def pages(self) -> str:
        if self.page_start is None:
            return "p.–"
        if self.page_end and self.page_end != self.page_start:
            return f"pp.{self.page_start}–{self.page_end}"
        return f"p.{self.page_start}"

    @property
    def citation(self) -> str:
        return f"[{self.doc_id}, {self.revision}, Clause {self.clause_no}, {self.pages}]"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


@contextmanager
def session():
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


CLAUSE_SELECT = """
SELECT c.id, c.doc_id, c.clause_no, c.heading, c.text, c.page_start, c.page_end,
       c.parent_no, c.path, d.revision, d.title, d.tier, d.synthetic
FROM clauses c JOIN documents d ON d.doc_id = c.doc_id
"""


def _row(r: sqlite3.Row) -> ClauseRow:
    return ClauseRow(**{k: r[k] for k in r.keys()})


def get_clauses(conn, ids: list[int]) -> list[ClauseRow]:
    if not ids:
        return []
    q = CLAUSE_SELECT + f" WHERE c.id IN ({','.join('?' * len(ids))})"
    by_id = {r["id"]: _row(r) for r in conn.execute(q, ids)}
    return [by_id[i] for i in ids if i in by_id]


def find_clause(conn, doc_id: str, clause_no: str) -> ClauseRow | None:
    r = conn.execute(CLAUSE_SELECT + " WHERE c.doc_id = ? AND c.clause_no = ?", (doc_id, clause_no)).fetchone()
    return _row(r) if r else None


def all_clauses(conn, doc_id: str | None = None) -> list[ClauseRow]:
    if doc_id:
        rows = conn.execute(CLAUSE_SELECT + " WHERE c.doc_id = ? ORDER BY c.ord", (doc_id,))
    else:
        rows = conn.execute(CLAUSE_SELECT + " ORDER BY c.doc_id, c.ord")
    return [_row(r) for r in rows]


def documents(conn) -> list[dict]:
    rows = conn.execute(
        """SELECT d.*, COUNT(c.id) AS clause_count
           FROM documents d LEFT JOIN clauses c ON c.doc_id = d.doc_id
           GROUP BY d.doc_id ORDER BY d.synthetic, d.doc_id"""
    )
    return [dict(r) for r in rows]


def log_query(conn, mode: str, query: str, answer: dict, cited: list[str], rejected: list[str], model: str) -> None:
    conn.execute(
        "INSERT INTO query_log (ts, mode, query, answer_json, cited, rejected, model) VALUES (?,?,?,?,?,?,?)",
        (datetime.now(timezone.utc).isoformat(timespec="seconds"), mode, query,
         json.dumps(answer, ensure_ascii=False), json.dumps(cited), json.dumps(rejected), model),
    )


def query_log(conn, limit: int = 500) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM query_log ORDER BY id DESC LIMIT ?", (limit,))]
