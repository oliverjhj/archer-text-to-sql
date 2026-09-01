import os
from functools import lru_cache

from pydantic import SecretStr
from langchain_ibm import WatsonxLLM

# Overridable so the evaluation suite can measure a different model without
# editing code. The default is the model the deployment actually runs.
DEFAULT_MODEL_ID = "mistralai/mistral-small-3-1-24b-instruct-2503"
DEFAULT_URL = "https://eu-gb.ml.cloud.ibm.com"

# Token budgets per task. These used to be a single shared value of 200, which
# was wrong in both directions at once:
#
#   the classifier returns "1" or "2" - one token - and was allocated 200
#   the SQL generator emits queries that can run past 200 and be truncated
#
# Sizing them separately costs nothing, because max_new_tokens is a ceiling
# rather than an allocation, and removes both problems.
CLASSIFIER_MAX_TOKENS = 5
SQL_MAX_TOKENS = 400
CHAT_MAX_TOKENS = 300


def _model_id() -> str:
    return os.environ.get("WATSONX_MODEL_ID", "").strip() or DEFAULT_MODEL_ID


def _build(max_new_tokens: int) -> WatsonxLLM:
    return WatsonxLLM(
        model_id=_model_id(),
        url=SecretStr(os.environ.get("WATSONX_URL", "").strip() or DEFAULT_URL),
        project_id=os.environ.get("PROJECT_ID", "").strip(),
        apikey=SecretStr(os.environ.get("IBM_API_KEY", "").strip()),
        params={"decoding_method": "greedy", "max_new_tokens": max_new_tokens},
    )


# Cached because building a client per request is pure overhead: the
# credentials and endpoint do not change while the process runs.
@lru_cache(maxsize=1)
def classifier_llm() -> WatsonxLLM:
    """Client for routing. Needs one token, so it is allowed five."""
    return _build(CLASSIFIER_MAX_TOKENS)


@lru_cache(maxsize=1)
def sql_llm() -> WatsonxLLM:
    """Client for SQL generation. Needs room for a complete query."""
    return _build(SQL_MAX_TOKENS)


@lru_cache(maxsize=1)
def chat_llm() -> WatsonxLLM:
    """Client for conversational replies."""
    return _build(CHAT_MAX_TOKENS)


_BY_TASK = {
    "classifier": classifier_llm,
    "sql": sql_llm,
    "chat": chat_llm,
}


def create_llm(task: str = "sql") -> WatsonxLLM:
    """
    Return the client configured for a task.

    A single entry point rather than three imported factories, because it is
    the seam the tests and the evaluation harness already patch. Defaulting to
    "sql" keeps every existing caller working unchanged.
    """
    try:
        return _BY_TASK[task]()
    except KeyError:
        raise ValueError(f"Unknown LLM task {task!r}; expected one of {sorted(_BY_TASK)}") from None
