from __future__ import annotations

from openai import AsyncOpenAI

from src.core.errors import EmbeddingError

__all__ = ['OpenRouterEmbedder']


class OpenRouterEmbedder:
    """Embedder backed by OpenRouter's OpenAI-compatible embeddings endpoint.

    Uses Qwen3-Embedding-8B with Matryoshka truncation (`dimensions`) and
    asymmetric retrieval (`input_type`: `search_document` at index time,
    `search_query` at query time).

    Works with any OpenAI-compatible embeddings endpoint via `base_url`.
    Set `input_type` to empty/None for providers that reject unknown request
    fields (e.g. the official OpenAI API with text-embedding-3-*).
    """

    def __init__(
        self,
        *,
        model: str,
        dimensions: int,
        batch_size: int,
        input_type: str | None = 'search_document',
        base_url: str | None = None,
        api_key: str | None = None,
        client: AsyncOpenAI | None = None,
    ) -> None:
        self._model = model
        self._dimensions = dimensions
        self._batch_size = batch_size
        self._input_type = input_type
        self._client = client or AsyncOpenAI(base_url=base_url, api_key=api_key)

    @property
    def dimension(self) -> int:
        return self._dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        out: list[list[float]] = []
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]
            extra_body = {'input_type': self._input_type} if self._input_type else None
            try:
                resp = await self._client.embeddings.create(
                    model=self._model,
                    input=batch,
                    dimensions=self._dimensions,
                    extra_body=extra_body,
                )
            except Exception as exc:
                raise EmbeddingError(
                    f'embedding provider failed on batch starting at index {i}: {exc}'
                ) from exc
            out.extend(d.embedding for d in resp.data)
        return out
