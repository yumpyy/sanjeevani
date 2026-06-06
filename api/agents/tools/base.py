"""Tool helpers shared by every LangChain tool in the backend.

Provides a tiny mixin for converting tool results to JSON-friendly dicts
so the graph can serialize them into state.
"""
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any

from langchain_core.tools import BaseTool


def to_jsonable(value: Any) -> Any:
    """Best-effort conversion of arbitrary tool output to JSON-friendly types."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if is_dataclass(value):
        return to_jsonable(asdict(value))
    if hasattr(value, "model_dump"):
        return to_jsonable(value.model_dump())
    if hasattr(value, "to_dict"):
        return to_jsonable(value.to_dict())
    if hasattr(value, "page_content") and hasattr(value, "metadata"):
        return {
            "page_content": value.page_content,
            "metadata": to_jsonable(value.metadata),
        }
    return str(value)


def dumps(value: Any) -> str:
    """JSON string used as the tool string-output for the LLM."""
    return json.dumps(to_jsonable(value), ensure_ascii=False, default=str)


class JsonSerializableTool(BaseTool):
    """Mixin: convert the raw return value to a JSON string.

    LangChain tool string-output is what reaches the LLM. Returning a JSON
    string keeps the schema strict while still being readable in prompts.
    """

    def _run(self, *args: Any, **kwargs: Any) -> str:  # type: ignore[override]
        result = self._run_jsonable(*args, **kwargs)
        return dumps(result)

    async def _arun(self, *args: Any, **kwargs: Any) -> str:  # type: ignore[override]
        result = await self._arun_jsonable(*args, **kwargs)
        return dumps(result)

    def _run_jsonable(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    async def _arun_jsonable(self, *args: Any, **kwargs: Any) -> Any:
        return self._run_jsonable(*args, **kwargs)
