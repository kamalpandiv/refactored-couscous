from typing import List

from langchain_core.embeddings import Embeddings
from langchain_experimental.text_splitter import SemanticChunker

from .base import BaseChunkingStrategy


class SemanticChunkingStrategy(BaseChunkingStrategy):
    def __init__(self, embedder: Embeddings):
        """
        Uses embeddings to determine natural break points.

        breakpoint_threshold_type="percentile":
        Calculates the difference in meaning between every sentence.
        If the difference is in the top 5% (95th percentile), it splits there.
        """
        self.splitter = SemanticChunker(
            embeddings=embedder,
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=95,  # Adjustable: Lower (e.g. 80) = More/Smaller chunks
        )

    def chunk(self, text: str) -> List[str]:
        # SemanticChunker expects a list of documents or a single string
        # It returns 'Document' objects, so we extract the page_content
        docs = self.splitter.create_documents([text])
        return [d.page_content for d in docs]
