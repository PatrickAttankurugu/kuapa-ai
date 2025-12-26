import pytest
from api.utils_fallback_retriever import FallbackRetriever

@pytest.fixture
def retriever():
    return FallbackRetriever()

def test_retriever_initialization(retriever):
    assert retriever is not None
    assert retriever.df is not None
    assert retriever.vectorizer is not None

def test_retriever_search_valid_query(retriever):
    results = retriever.search("nitrogen deficiency in maize")
    assert isinstance(results, list)
    assert len(results) > 0
    for result in results:
        assert len(result) == 3
        chunk, score, source = result
        assert isinstance(chunk, str)
        assert isinstance(score, float)
        assert isinstance(source, str)

def test_retriever_search_empty_query(retriever):
    results = retriever.search("")
    assert results == []

def test_retriever_search_with_k_parameter(retriever):
    results = retriever.search("maize", k=3)
    assert len(results) <= 3

def test_retriever_search_returns_sorted_results(retriever):
    results = retriever.search("nitrogen deficiency")
    if len(results) > 1:
        scores = [score for _, score, _ in results]
        assert scores == sorted(scores, reverse=True)
