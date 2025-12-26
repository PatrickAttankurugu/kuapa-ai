import pytest
from api.rag import retrieve_context

def test_retrieve_context_valid_query():
    results = retrieve_context("What are symptoms of nitrogen deficiency?")
    assert isinstance(results, list)
    assert len(results) > 0

def test_retrieve_context_empty_query():
    results = retrieve_context("")
    assert isinstance(results, list)

def test_retrieve_context_returns_tuples():
    results = retrieve_context("maize farming")
    for result in results:
        assert len(result) == 3
        chunk, score, source = result
        assert isinstance(chunk, str)
        assert isinstance(score, float)
        assert isinstance(source, str)
