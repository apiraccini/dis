from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    # Postgres (raw document metadata: documents, tags, chunks)
    postgres_host: str = 'db'
    postgres_port: int = 5432
    postgres_user: str = 'dis'
    postgres_password: str = 'dis'
    postgres_db: str = 'dis'

    # Qdrant (vectors + payload filtering by document/tag)
    qdrant_url: str = 'http://qdrant:6333'
    qdrant_api_key: str | None = None
    qdrant_collection: str = 'documents'

    # Embeddings — model NOT decided yet; left empty until the SDD session.
    openai_api_key: str | None = None
    embedding_model: str | None = None
    embedding_dimensions: int | None = None

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
