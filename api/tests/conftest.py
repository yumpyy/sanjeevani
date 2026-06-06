"""Shared pytest fixtures.

The supervisor graph's checkpointer is normally Postgres, which the CI
environment may not have. The ``graph_factory`` fixture prefers Postgres
when ``POSTGRES_URL`` is set; otherwise it falls back to ``MemorySaver``
so unit tests stay self-contained.

LLM calls are stubbed via monkey-patched node functions in each test.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Allow `import config` etc. from this directory.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def graph_factory():
    """Return a callable that builds either the real supervisor graph or
    one backed by a non-persistent checkpointer.

    Usage::

        def test_foo(graph_factory):
            graph = graph_factory(use_memory=True)
            ...
    """
    from langgraph.checkpoint.memory import MemorySaver

    def _build(use_memory: bool = False):
        if use_memory or not os.getenv("POSTGRES_URL"):
            checkpointer = MemorySaver()
        else:
            from config import get_checkpointer

            checkpointer = get_checkpointer()
        from agents.physician_graph import build_physician_graph
        from agents.therapist_graph import build_therapist_graph

        return {
            "physician": build_physician_graph(checkpointer),
            "therapist": build_therapist_graph(checkpointer),
        }

    return _build
