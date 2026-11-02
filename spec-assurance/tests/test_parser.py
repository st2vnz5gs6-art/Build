"""Clause parsing on the real SUB-03-034 and SUB-01-012 PDFs."""

import re

from spec_assurance import store
from spec_assurance.ingest.clauses import plausible_next


def test_documents_metadata(conn):
    docs = {d["doc_id"]: d for d in store.documents(conn)}
    assert docs["SUB-03-034"]["revision"] == "Issue 5"
    assert "275kV & 400kV" in docs["SUB-03-034"]["title"]
    assert docs["SUB-01-012"]["revision"] == "Issue 4"


def test_known_clauses_parsed(conn):
    bund = store.find_clause(conn, "SUB-03-034", "12.9.1")
    assert bund.heading == "Bund Systems"
    assert bund.page_start == 29
    assert bund.parent_no == "12.9"
    assert "115% of total oil content" in bund.text
    assert "not less than 225mm thick" in bund.text
    assert store.find_clause(conn, "SUB-03-034", "10.4.6").heading.startswith("Discharges to Surface Water")
    assert store.find_clause(conn, "SUB-03-034", "12.8.3.2").heading == "Oil-Petrol Separators"


def test_numbering_is_in_order(conn):
    for doc in ("SUB-03-034", "SUB-01-012"):
        nums = [c.clause_no for c in store.all_clauses(conn, doc)]
        assert len(nums) == len(set(nums))
        for a, b in zip(nums, nums[1:]):
            assert plausible_next([int(x) for x in a.split(".")], [int(x) for x in b.split(".")]), (doc, a, b)


def test_no_page_furniture_in_clause_text(conn):
    for c in store.all_clauses(conn):
        assert not re.search(r"Page \d+ of \d+", c.text), c.citation
        assert "Internal Use" not in c.text, c.citation


def test_tables_kept_with_their_clause(conn):
    concrete = store.find_clause(conn, "SUB-03-034", "12.5.3")
    assert "[Table]" in concrete.text
    assert "Blinding Layer | C16/20" in concrete.text


def test_list_numbers_not_mistaken_for_clauses():
    assert not plausible_next([12, 9, 1], [3])
    assert not plausible_next([12, 9, 1], [12, 9, 5])
    assert plausible_next([12, 9, 1], [12, 9, 2])
    assert plausible_next([12, 9, 7], [12, 10])
    assert plausible_next([12, 17], [13, 1])
