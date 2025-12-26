from typing import List, Tuple
from .utils_fallback_retriever import FallbackRetriever

_retriever = None

def _get_retriever():
    global _retriever
    if _retriever is None:
        _retriever = FallbackRetriever()
    return _retriever

def retrieve_context(query: str) -> List[Tuple[str, float, str]]:
    r = _get_retriever()
    return r.search(query)
