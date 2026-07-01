from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    # Postgres (document metadata + parsed text; chunks live in Qdrant, not here)
    postgres_host: str = 'db'
    postgres_port: int = 5432
    postgres_user: str = 'dis'
    postgres_password: str = 'dis'
    postgres_db: str = 'dis'

    # Qdrant (vectors + payload filtering by document/tag)
    qdrant_url: str = 'http://qdrant:6333'
    qdrant_collection: str = 'documents'

    # Embeddings via OpenRouter (OpenAI-compatible API). Only the key is secret;
    # model/dimensions/chunk params live here with defaults.
    openrouter_api_key: str | None = None
    embedding_base_url: str = 'https://openrouter.ai/api/v1'
    embedding_model: str = 'qwen/qwen3-embedding-8b'
    embedding_dimensions: int = 1536
    # Qwen3 supports asymmetric retrieval via input_type.
    embedding_input_type_document: str = 'search_document'
    embedding_input_type_query: str = 'search_query'
    embedding_batch_size: int = 64

    # Chunking (semchunk, token-based).
    chunk_size_tokens: int = 1024
    chunk_overlap_tokens: int = 0

    # When true, ingestion uses a deterministic in-process fake embedder (e2e only).
    use_fake_embedder: bool = False

    # MCP server auth (Bearer token on the /mcp endpoint)
    mcp_api_key: str = 'dev-mcp-key-change-me'

    # CORS for the REST API (frontend origin(s))
    backend_cors_origins: list[str] = ['http://localhost:5173', 'http://localhost:3000']

    @property
    def database_url(self) -> str:
        return (
            f'postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}'
            f'@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}'
        )


settings = Settings()
