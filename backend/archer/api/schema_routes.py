import sqlite3
import logging

from fastapi import APIRouter, Depends, Request

from ..auth.jwt import get_current_user
from ..core.limiter import limiter
from ..db.database import database_path

router = APIRouter()

# Columns the model is told to return by default, and which most answers are
# built from. Surfaced separately so the reference reflects what a user will
# actually see rather than all 37 columns undifferentiated.
COMMON_COLUMNS = {
    "customer_name",
    "document_date",
    "document_number",
    "item_group",
    "item_description",
    "revenue",
    "end_user_company_name",
    "quantity",
}

# Values worth knowing before asking a question. These mirror the COLUMN VALUES
# section of the SQL prompt: if a user has to guess whether a flag is 'Yes' or
# 'Y', so did the model, and that was a real source of wrong answers.
KNOWN_VALUES = {
    "document_type": ["Invoice", "Credit"],
    "item_group": ["IBM SOFT", "IBM SERV", "IBM CCHW"],
    "multi_year_deal_flag_so": ["Yes", "No"],
}


@router.get("/api/schema")
@limiter.limit("30/minute")
async def get_schema(request: Request, username: str = Depends(get_current_user)):
    """
    Describe the dataset a visitor is querying.

    A demo where the user cannot see the column names is a guessing game, and
    the questions people invent when guessing are the ones that come back
    empty. This is read straight from the database rather than from a hardcoded
    list, so it cannot drift from what is actually there.
    """
    conn = None
    try:
        conn = sqlite3.connect(f"file:{database_path()}?mode=ro", uri=True)
        cursor = conn.cursor()

        columns = [
            {"name": row[1], "type": row[2] or "TEXT", "common": row[1] in COMMON_COLUMNS}
            for row in cursor.execute("PRAGMA table_info(sales_data)")
        ]
        rows = cursor.execute("SELECT COUNT(*) FROM sales_data").fetchone()[0]
        date_from, date_to = cursor.execute(
            "SELECT MIN(document_date), MAX(document_date) FROM sales_data"
        ).fetchone()

        return {
            "table": "sales_data",
            "row_count": rows,
            "date_from": date_from,
            "date_to": date_to,
            "columns": columns,
            "known_values": KNOWN_VALUES,
        }
    except sqlite3.Error as exc:
        logging.error("Could not read schema: %s", exc)
        return {"table": "sales_data", "row_count": 0, "columns": [], "known_values": {}}
    finally:
        if conn:
            conn.close()
