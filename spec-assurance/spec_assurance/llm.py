"""Claude client, the citation-only system prompt and the structured answer schemas.

Every call gets the retrieved clauses labelled [C1]..[Cn] and must answer in a
fixed JSON shape that refers to them by label. `citations.verify` then checks
each label and quote against the database before anything is shown.
"""

from __future__ import annotations

import base64
import json
import os
from typing import Literal

from pydantic import BaseModel, Field

from . import config, hierarchy
from .store import ClauseRow

try:  # Corporate networks re-sign TLS; use the Windows certificate store when available.
    import truststore

    truststore.inject_into_ssl()
except Exception:
    pass


SYSTEM_PROMPT = """You are the design assurance assistant for a Principal Civil & Structural Engineer at SP Transmission (HVDC, Eastern Green Link 1). You check queries, RFIs and contractor submissions against a library of SP Energy Networks civil and structural specifications.

You are given numbered library clauses, each labelled [C1], [C2] and so on, with its document, revision, clause number and page. These clauses are the only evidence you may use.

Rules:
1. State a requirement only if a supplied clause contains it. Never rely on memory of a standard for a requirement.
2. Every requirement you state carries its label, e.g. "Bunds shall contain 115% of oil content [C2]".
3. Quotes are copied character for character from the clause text: no paraphrase, no joining of separate sentences, no added words. Keep each quote to the shortest passage that carries the requirement (normally one or two sentences).
4. Keep three things apart: what the specification says (quotes), your interpretation of how it applies, and gaps or conflicts.
5. If the clauses do not answer the question, or only partly answer it, say so plainly. Use coverage "not_covered" or "partial" and name the standard or guidance that would likely govern (e.g. BS EN 1992-1-1 / BS 8500-1 for cover) without stating its requirements.
6. Note the scope of each document. The library holds specifications for different substation types (secondary, primary/33kV, 132kV, 275/400kV). Prefer the document whose scope matches the question, and point out where another document says something different.
7. Where two clauses disagree, report the conflict and which governs under this precedence: {precedence}. Documents in the same tier: say that clarification from SPEN Engineering Design & Standards is needed.
8. British English. Plain, direct engineering language. No filler, no hedging beyond what the evidence requires.
"""


def system_prompt() -> str:
    return SYSTEM_PROMPT.format(precedence=hierarchy.precedence_text())


# --------------------------------------------------------------------------- schemas

class Quote(BaseModel):
    ref: str = Field(description="Clause label, e.g. C3")
    quote: str = Field(description="Verbatim passage copied from that clause")


Coverage = Literal["covered", "partial", "not_covered"]


class AskAnswer(BaseModel):
    answer: str = Field(description="Direct answer in 1–4 sentences; every requirement tagged with its [Cn] label")
    spec_says: list[Quote] = Field(description="Verbatim quotes that support the answer")
    interpretation: str = Field(description="How the quoted requirements apply to the question; empty if nothing to add")
    gaps_conflicts: list[str] = Field(description="Gaps in coverage, conflicts between documents, scope caveats")
    coverage: Coverage
    likely_standard: str = Field(description="If partial or not covered: the standard likely to govern; else empty")


class RFIAnswer(BaseModel):
    rfi_summary: str = Field(description="One-sentence restatement of what the RFI asks")
    position: Literal["Compliant", "Non-compliant", "Clarification needed"]
    position_basis: str = Field(description="Why, with [Cn] labels")
    spec_says: list[Quote]
    interpretation: str
    gaps_conflicts: list[str]
    coverage: Coverage
    likely_standard: str
    draft_response: str = Field(description="Suggested RFI response wording for issue to the contractor, citing clauses as [Cn]")


class ExtractedStatement(BaseModel):
    location: str = Field(description="Where it is: section/page of a report, or note number / grid reference / title block on a drawing")
    statement: str = Field(description="The technical statement, copied from the document")
    topic: str = Field(description="Short search phrase for the requirement it relates to, e.g. 'bund capacity'")


class Extraction(BaseModel):
    document_kind: Literal["report", "calculation", "design statement", "drawing", "other"]
    title_block: str = Field(description="Drawing/document number, revision and status if shown; else empty")
    statements: list[ExtractedStatement]


class Finding(BaseModel):
    statement_id: int
    refs: list[str] = Field(description="Clause labels relied on, e.g. ['C2']")
    quote: str = Field(description="Verbatim passage from the governing clause; empty if not covered")
    finding: str = Field(description="What the statement says against what the clause requires")
    rag: Literal["Green", "Amber", "Red", "Not covered"]
    comment: str = Field(description="Reviewer comment to issue to the contractor")


class ReviewBatch(BaseModel):
    findings: list[Finding]


class MissingNote(BaseModel):
    requirement: str = Field(description="What the specification requires the drawing or document to state")
    ref: str
    quote: str
    status: Literal["Missing", "Present", "Unclear"]


class MissingNotes(BaseModel):
    items: list[MissingNote]


# --------------------------------------------------------------------------- client

class LLMUnavailable(RuntimeError):
    pass


def mode() -> str:
    if config.LLM_MODE in ("live", "mock"):
        return config.LLM_MODE
    return "live" if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN") else "mock"


_client = None


def client():
    global _client
    if _client is None:
        import anthropic

        _client = anthropic.Anthropic(max_retries=3, timeout=300)
    return _client


def format_clauses(clauses: list[ClauseRow]) -> str:
    out = []
    for i, c in enumerate(clauses, 1):
        out.append(
            f'<clause label="C{i}" doc="{c.doc_id}" revision="{c.revision}" clause="{c.clause_no}" '
            f'pages="{c.pages}" heading="{c.heading}" section="{c.path}" tier="{c.tier}">\n'
            f"Document: {c.title}\n{c.text}\n</clause>"
        )
    return "\n\n".join(out)


def call(schema: type[BaseModel], user_content: str | list, max_tokens: int = 16000) -> BaseModel:
    """One structured Claude call. Raises LLMUnavailable on refusal or unusable output."""
    import anthropic

    content = user_content if isinstance(user_content, list) else [{"type": "text", "text": user_content}]
    try:
        resp = client().beta.messages.parse(
            model=config.CLAUDE_MODEL,
            max_tokens=max_tokens,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=[{"type": "text", "text": system_prompt(), "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": content}],
            output_config={"effort": config.CLAUDE_EFFORT},
            output_format=schema,
        )
    except anthropic.AuthenticationError as exc:
        raise LLMUnavailable("Claude API key rejected — check ANTHROPIC_API_KEY in .env") from exc
    except anthropic.APIConnectionError as exc:
        raise LLMUnavailable("Cannot reach the Claude API — check network / proxy settings") from exc
    except anthropic.APIStatusError as exc:
        raise LLMUnavailable(f"Claude API error {exc.status_code}: {exc.message}") from exc
    if resp.stop_reason == "refusal":
        raise LLMUnavailable("Claude declined this request")
    if resp.stop_reason == "max_tokens":
        raise LLMUnavailable("Answer was cut off (max tokens) — try a narrower request")
    if resp.parsed_output is None:
        raise LLMUnavailable("Claude returned an answer that did not match the expected format")
    return resp.parsed_output


def image_block(data: bytes, media_type: str = "image/png") -> dict:
    return {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": base64.b64encode(data).decode()}}


def transcribe_image(data: bytes, media_type: str = "image/png") -> str:
    """Claude vision fallback: transcribe every piece of text on a drawing sheet."""

    class Transcript(BaseModel):
        text: str

    prompt = ("Transcribe all text on this engineering drawing exactly as written: general and specific notes "
              "(keep their numbers), title block fields, material callouts, loads, referenced standards and "
              "annotations. One item per line. Do not describe geometry and do not add anything that is not written.")
    out = call(Transcript, [image_block(data, media_type), {"type": "text", "text": prompt}])
    return out.text


def to_json(model: BaseModel) -> dict:
    return json.loads(model.model_dump_json())
