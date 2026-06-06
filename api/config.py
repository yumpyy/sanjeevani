"""Runtime configuration for the Sanjeevani API.

LLM: a single OpenAI-compatible client. We default to the Alibaba
Cloud DashScope ``/compatible-mode/v1`` endpoint (which speaks the
OpenAI Chat Completions protocol), but the same factory works for
OpenAI, Groq, Together, OpenRouter, vLLM, llama.cpp, etc.

Set the following in ``api/.env``:

* ``DASHSCOPE_API_KEY``   — required
* ``DASHSCOPE_MODEL``     — chat model name (default ``deepseek-v4-flash``)
* ``DASHSCOPE_BASE_URL``  — endpoint URL (default
  ``https://dashscope-intl.aliyuncs.com/compatible-mode/v1``)

Embeddings: an OpenAI-compatible embeddings client
(``DASHSCOPE_EMBEDDING_MODEL``). The DashScope endpoint also exposes
an OpenAI-compatible ``/embeddings`` route.
"""
from dotenv import load_dotenv
from os import environ
from pydantic import BaseModel

load_dotenv()


DEFAULT_DASHSCOPE_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
DEFAULT_DASHSCOPE_MODEL = "deepseek-v4-flash"


class Config(BaseModel):
    dashscope_api_key: str = ""
    dashscope_model: str = DEFAULT_DASHSCOPE_MODEL
    dashscope_base_url: str = DEFAULT_DASHSCOPE_BASE_URL
    dashscope_embedding_model: str = "text-embedding-v3"
    max_pubmed_results: int = 8
    cache_ttl_days: int = 7
    chroma_persist_directory: str = "./chroma_db"
    postgres_url: str = "postgresql://sanjeevani:sanjeevani@localhost:5432/sanjeevani"


DEFAULT_POSTGRES_URL = "postgresql://sanjeevani:sanjeevani@localhost:5432/sanjeevani"


def _build_config() -> Config:
    return Config(
        dashscope_api_key=environ.get("DASHSCOPE_API_KEY", ""),
        dashscope_model=environ.get("DASHSCOPE_MODEL", DEFAULT_DASHSCOPE_MODEL),
        dashscope_base_url=environ.get("DASHSCOPE_BASE_URL", DEFAULT_DASHSCOPE_BASE_URL),
        dashscope_embedding_model=environ.get(
            "DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v3"
        ),
        max_pubmed_results=int(environ.get("MAX_PUBMED_RESULTS", "8")),
        cache_ttl_days=int(environ.get("CACHE_TTL_DAYS", "7")),
        chroma_persist_directory=environ.get("CHROMA_PERSIST_DIRECTORY", "./chroma_db"),
        postgres_url=environ.get("POSTGRES_URL", DEFAULT_POSTGRES_URL),
    )


config = _build_config()


def _require_api_key() -> str:
    if not config.dashscope_api_key:
        raise RuntimeError(
            "DASHSCOPE_API_KEY is not set. Set it in api/.env to start the API."
        )
    return config.dashscope_api_key


def get_llm():
    """Return a ``ChatOpenAI`` instance pointed at the DashScope-compatible
    endpoint. The instance is rebuilt on every call (cheap) so env-var
    changes are picked up on the next request.
    """
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=config.dashscope_model,
        api_key=_require_api_key(),
        base_url=config.dashscope_base_url,
        temperature=0.3,
        max_retries=2,
    )


def get_embeddings():
    """Return an OpenAI-compatible embeddings client pointed at DashScope."""
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=config.dashscope_embedding_model,
        api_key=_require_api_key(),
        base_url=config.dashscope_base_url,
    )


get_chat_model = get_llm


_checkpointer = None


def get_checkpointer():
    """Build the LangGraph checkpointer.

    Uses ``langgraph-checkpoint-postgres`` against the Postgres instance
    configured by ``POSTGRES_URL``. The checkpointer (and its underlying
    connection) is cached at module level so it lives for the lifetime of
    the process. Hard-fails at startup if the database is unreachable.
    """
    global _checkpointer
    if _checkpointer is not None:
        return _checkpointer

    try:
        from langgraph.checkpoint.postgres import PostgresSaver
        from psycopg import Connection
        from psycopg.rows import dict_row
    except ImportError as e:
        raise RuntimeError(
            "langgraph-checkpoint-postgres is not installed. Run `uv sync`."
        ) from e

    url = config.postgres_url
    if not url:
        raise RuntimeError("POSTGRES_URL is not set. Aborting startup.")

    print(f"Connecting to Postgres checkpointer: {url.split('@')[-1]}")
    conn = Connection.connect(
        url, autocommit=True, prepare_threshold=0, row_factory=dict_row
    )
    checkpointer = PostgresSaver(conn)
    checkpointer.setup()  # idempotent: creates tables on first run
    _checkpointer = checkpointer
    return _checkpointer
