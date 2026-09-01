"""
Unit tests for SQL sanitisation behaviour in archer.ai.sql_generator.

These tests exercise the sanitisation and extraction logic inside generate_sql()
without calling any real LLM or network service.  The LLM argument is replaced
with a MagicMock whose .invoke() method returns a controlled SQL string so that
the post-LLM sanitisation code path is exercised in isolation.

Sanitisation rules under test (sql_generator.py):
  - The SELECT-line extractor: finds the first line containing "SELECT".
  - The re.split sanitiser: splits on ;  #  --  /*  */  or a newline followed
    by ATTACH / DETACH / PRAGMA (case-insensitive), then takes element [0].
"""

import pytest
from unittest.mock import MagicMock

from archer.ai.sql_generator import generate_sql


def _mock_llm(sql_response: str) -> MagicMock:
    """Return a MagicMock LLM whose .invoke() yields the given string."""
    llm = MagicMock()
    llm.invoke.return_value = sql_response
    return llm


SCHEMA = "customer_name, revenue"


# ---------------------------------------------------------------------------
# Extraction gate: no SELECT in LLM output -> empty string returned
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_no_select_in_response_returns_empty() -> None:
    """LLM response with no SELECT line yields an empty SQL string."""
    llm = _mock_llm("I cannot generate that query.")
    sql, _ = generate_sql(llm, "some question", SCHEMA)
    assert sql == ""


# ---------------------------------------------------------------------------
# Clean SELECT passes through unchanged
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_clean_select_is_returned_unchanged() -> None:
    """A well-formed SELECT statement is returned as-is."""
    raw = "SELECT customer_name, revenue FROM sales_data LIMIT 10"
    sql, _ = generate_sql(_mock_llm(raw), "show me customers", SCHEMA)
    assert sql == raw


# ---------------------------------------------------------------------------
# Semicolon injection: statement is truncated at the first semicolon
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_semicolon_truncates_at_first_statement() -> None:
    """A semicolon causes the output to be truncated to the first statement."""
    raw = "SELECT revenue FROM sales_data; DROP TABLE sales_data"
    sql, _ = generate_sql(_mock_llm(raw), "revenue", SCHEMA)
    assert sql == "SELECT revenue FROM sales_data"
    assert "DROP" not in sql


# ---------------------------------------------------------------------------
# Hash comment injection
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_hash_comment_is_stripped() -> None:
    """A hash character causes the output to be truncated at that point."""
    raw = "SELECT revenue FROM sales_data # injected comment"
    sql, _ = generate_sql(_mock_llm(raw), "revenue", SCHEMA)
    assert sql == "SELECT revenue FROM sales_data"


# ---------------------------------------------------------------------------
# SQL line-comment injection (--)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_double_dash_comment_is_stripped() -> None:
    """A double-dash SQL comment causes truncation at that point."""
    raw = "SELECT revenue FROM sales_data -- injected"
    sql, _ = generate_sql(_mock_llm(raw), "revenue", SCHEMA)
    assert sql == "SELECT revenue FROM sales_data"


# ---------------------------------------------------------------------------
# Block comment injection (/* ... */)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_block_comment_open_is_stripped() -> None:
    """An opening block-comment marker causes truncation."""
    raw = "SELECT revenue FROM sales_data /* comment"
    sql, _ = generate_sql(_mock_llm(raw), "revenue", SCHEMA)
    assert sql == "SELECT revenue FROM sales_data"


@pytest.mark.unit
def test_block_comment_close_is_stripped() -> None:
    """A closing block-comment marker causes truncation."""
    raw = "SELECT revenue FROM sales_data */ trailing"
    sql, _ = generate_sql(_mock_llm(raw), "revenue", SCHEMA)
    assert sql == "SELECT revenue FROM sales_data"


# ---------------------------------------------------------------------------
# ATTACH / DETACH / PRAGMA on a new line after SELECT are blocked
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_attach_on_newline_is_stripped() -> None:
    """ATTACH DATABASE on a new line after a SELECT is truncated."""
    raw = "SELECT revenue FROM sales_data\nATTACH DATABASE 'evil.db' AS evil"
    sql, _ = generate_sql(_mock_llm(raw), "revenue", SCHEMA)
    assert "ATTACH" not in sql.upper()
    assert sql.startswith("SELECT")


@pytest.mark.unit
def test_detach_on_newline_is_stripped() -> None:
    """DETACH on a new line after a SELECT is truncated."""
    raw = "SELECT revenue FROM sales_data\nDETACH evil"
    sql, _ = generate_sql(_mock_llm(raw), "revenue", SCHEMA)
    assert "DETACH" not in sql.upper()
    assert sql.startswith("SELECT")


@pytest.mark.unit
def test_pragma_on_newline_is_stripped() -> None:
    """PRAGMA on a new line after a SELECT is truncated."""
    raw = "SELECT revenue FROM sales_data\nPRAGMA journal_mode=WAL"
    sql, _ = generate_sql(_mock_llm(raw), "revenue", SCHEMA)
    assert "PRAGMA" not in sql.upper()
    assert sql.startswith("SELECT")


# ---------------------------------------------------------------------------
# Markdown code-fence markers are removed from the SELECT line
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_code_fence_prefix_is_stripped() -> None:
    """A ```sql prefix before SELECT is removed during extraction."""
    raw = "```sql SELECT revenue FROM sales_data LIMIT 5"
    sql, _ = generate_sql(_mock_llm(raw), "revenue", SCHEMA)
    assert sql == "SELECT revenue FROM sales_data LIMIT 5"


@pytest.mark.unit
def test_code_fence_suffix_is_stripped() -> None:
    """A trailing ``` after SELECT is removed during extraction."""
    raw = "SELECT revenue FROM sales_data LIMIT 5```"
    sql, _ = generate_sql(_mock_llm(raw), "revenue", SCHEMA)
    assert sql == "SELECT revenue FROM sales_data LIMIT 5"


# ---------------------------------------------------------------------------
# Edge case: empty string from LLM
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_empty_llm_response_returns_empty() -> None:
    """An empty LLM response yields an empty SQL string."""
    sql, _ = generate_sql(_mock_llm(""), "anything", SCHEMA)
    assert sql == ""
