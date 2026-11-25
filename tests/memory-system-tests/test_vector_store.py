import pytest
from jarvis.memory.vector_store import vector_store

def test_vector_store_initializes():
    vs = vector_store
    assert vs is not None
