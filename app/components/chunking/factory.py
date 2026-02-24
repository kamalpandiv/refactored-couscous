from typing import Literal

from langchain_core.embeddings import Embeddings

from .paragraph import ParagraphChunkingStrategy
from .recursive import RecursiveChunkingStrategy
from .semantic import SemanticChunkingStrategy
from .token_safe import TokenSafeMixin

ChunkingStrategyType = Literal["recursive", "semantic", "paragraph"]


class TokenSafeChunker(TokenSafeMixin):
    def __init__(self, base_strategy):
        super().__init__()
        self.base_strategy = base_strategy

    def chunk(self, text: str):
        chunks = self.base_strategy.chunk(text)
        return self.enforce_token_limit(chunks)


class ChunkingFactory:
    @staticmethod
    def create(
        strategy: ChunkingStrategyType,
        embedder: Embeddings = None,
        token_safe: bool = True,
    ):
        # 1. Select the Base Strategy
        if strategy == "semantic":
            if not embedder:
                raise ValueError("Semantic strategy requires embedder")
            base_strategy = SemanticChunkingStrategy(embedder)

        elif strategy == "paragraph":
            # New Paragraph Strategy
            base_strategy = ParagraphChunkingStrategy(chunk_size=1000, overlap_size=200)

        else:
            # Default to Recursive
            base_strategy = RecursiveChunkingStrategy()

        # 2. Apply Token Safety Wrapper (Optional)
        if token_safe:
            return TokenSafeChunker(base_strategy)

        return base_strategy
