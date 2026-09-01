import re
from datetime import datetime
from typing import Tuple

from .prompts import render

def generate_sql(llm, user_query_escaped: str, schema_text: str) -> Tuple[str, str]:
    """
    Generate SQL query from user question.
    
    Args:
        llm: WatsonxLLM instance
        user_query_escaped: User query with escaped special characters
        schema_text: Comma-separated list of column names
        
    Returns:
        Tuple[str, str]: (clean_sql, generated_response)
    """
    today_str = datetime.today().strftime('%Y-%m-%d')
    
    prompt = render(
        "sql_generator",
        TODAY=today_str,
        SCHEMA=schema_text,
        USER_QUERY=user_query_escaped,
    )

    generated_response = llm.invoke(prompt)
    
    clean_sql = ""
    for line in generated_response.split('\n'):
        if "SELECT" in line.upper():
            clean_sql = line.replace("```sql", "").replace("```", "").strip()
            break
    
    if not clean_sql:
        return "", generated_response
    
    # Enhanced SQL sanitisation to block non-SELECT queries
    clean_sql = re.split(r';|#|--|/\*|\*/|\n\s*(?:ATTACH|DETACH|PRAGMA)', clean_sql, flags=re.IGNORECASE)[0].strip()
    
    return clean_sql, generated_response

