import re
import logging

from .prompts import render

def classify_query(llm, user_query_escaped: str) -> str:
    """
    Classify user query as either database query (1) or general chat (2).
    
    Args:
        llm: WatsonxLLM instance
        user_query_escaped: User query with escaped special characters
        
    Returns:
        str: "1" for database query, "2" for general chat
    """
    classifier_prompt = render("classifier", USER_QUERY=user_query_escaped)
    
    raw_classification = llm.invoke(classifier_prompt).strip()
    logging.info(f"AI Classification Output: {raw_classification}")
    
    match = re.search(r'[12]', raw_classification)
    route_decision = match.group(0) if match else "2"
    logging.info(f"Route Decision: {route_decision} ({'DATA QUERY' if route_decision == '1' else 'GENERAL CHAT'})")
    
    return route_decision

