from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    id: str
    text: str
    vector: Optional[List[float]] = None
    metadata: Dict = Field(default_factory=dict)  # Stores 'source', 'page', 'author'
    score: Optional[float] = None  # For search results
