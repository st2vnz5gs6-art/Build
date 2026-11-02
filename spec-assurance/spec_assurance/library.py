"""Library ingestion: parse files in /library into the store and rebuild the indexes."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import config, embed, hierarchy, store
from .ingest.clauses import hierarchy_path, parse_toc, segment
from .ingest.docx_parser import parse_docx
from .ingest.pdf_parser import ParsedDoc, parse_pdf

SUPPORTED = {".pdf", ".docx"}
SYNTHETIC_MARK = "DEMO – NOT SPT CONTROLLED DOCUMENT"


@dataclass
class IngestResult:
    filename: str
    doc_id: str
    status: str  # ingested | unchanged | failed
    clauses: int = 0
    message: str = ""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_file(path: Path) -> ParsedDoc:
    if path.suffix.lower() == ".pdf":
        return parse_pdf(path)
    if path.suffix.lower() == ".docx":
        return parse_docx(path)
    raise ValueError(f"Unsupported file type: {path.suffix}")


def ingest_file(conn, path: Path, digest: str | None = None) -> IngestResult:
    digest = digest or sha256(path)
    parsed = parse_file(path)
    clauses = segment(parsed.blocks, parse_toc(parsed.toc_lines))
    if not clauses:
        return IngestResult(path.name, parsed.doc_id, "failed", message="No numbered clauses found")
    paths = hierarchy_path(clauses)
    synthetic = SYNTHETIC_MARK.lower() in " ".join(parsed.page_texts[:2]).lower()
    tier = hierarchy.tier_for(parsed.doc_id)

    conn.execute("DELETE FROM documents WHERE doc_id = ? OR filename = ?", (parsed.doc_id, path.name))
    conn.execute(
        "INSERT INTO documents (doc_id, title, revision, filename, sha256, pages, tier, synthetic, ingested_at)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        (parsed.doc_id, parsed.title, parsed.revision, path.name, digest, parsed.pages, tier, int(synthetic),
         datetime.now(timezone.utc).isoformat(timespec="seconds")),
    )
    seen: set[str] = set()
    for c in clauses:
        if c.clause_no in seen:  # repeated numbering (e.g. appendix restarts) — keep the first
            continue
        seen.add(c.clause_no)
        conn.execute(
            "INSERT INTO clauses (doc_id, clause_no, heading, text, page_start, page_end, parent_no, path, ord)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (parsed.doc_id, c.clause_no, c.heading, c.text, c.page_start, c.page_end, c.parent_no,
             paths.get(c.clause_no, ""), c.order),
        )
    return IngestResult(path.name, parsed.doc_id, "ingested", len(seen))


def reindex(force: bool = False, progress=None) -> list[IngestResult]:
    """Ingest new/changed files in /library, drop removed ones, rebuild the vector index."""
    files = sorted(p for p in config.LIBRARY_DIR.rglob("*") if p.suffix.lower() in SUPPORTED and not p.name.startswith("~$"))
    results: list[IngestResult] = []
    with store.session() as conn:
        known = {r["filename"]: r for r in conn.execute("SELECT filename, sha256, doc_id FROM documents")}
        for i, path in enumerate(files):
            if progress:
                progress(i / max(len(files), 1), f"Parsing {path.name}")
            digest = sha256(path)
            if not force and path.name in known and known[path.name]["sha256"] == digest:
                n = conn.execute("SELECT COUNT(*) FROM clauses WHERE doc_id = ?", (known[path.name]["doc_id"],)).fetchone()[0]
                results.append(IngestResult(path.name, known[path.name]["doc_id"], "unchanged", n))
                continue
            try:
                results.append(ingest_file(conn, path, digest))
            except Exception as exc:  # one bad file must not stop the rest
                results.append(IngestResult(path.name, "", "failed", message=str(exc)))
            conn.commit()
        present = {p.name for p in files}
        for filename in set(known) - present:
            conn.execute("DELETE FROM documents WHERE filename = ?", (filename,))
        if progress:
            progress(0.95, "Building semantic index")
        embed.build_index(store.all_clauses(conn))
    if progress:
        progress(1.0, "Done")
    return results


def save_upload(name: str, data: bytes) -> Path:
    dest = config.LIBRARY_DIR / Path(name).name
    dest.write_bytes(data)
    return dest
