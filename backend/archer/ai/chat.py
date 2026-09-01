from ..db.database import dataset_date_range
from .prompts import render


def generate_chat_response(llm, user_query_escaped: str) -> str:
    """
    Generate general chat response using Archer persona.
    
    Args:
        llm: WatsonxLLM instance
        user_query_escaped: User query with escaped special characters
        
    Returns:
        str: Chat response
    """
    date_from, date_to = dataset_date_range()
    chat_prompt = render(
        "chat",
        USER_QUERY=user_query_escaped,
        DATE_FROM=date_from or "the start of the dataset",
        DATE_TO=date_to or "the most recent record",
    )
    
    chat_response = llm.invoke(chat_prompt).strip()
    return chat_response

