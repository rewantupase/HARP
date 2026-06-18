from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date


class RankedChunkHit(BaseModel):
    chunk_id: UUID
    score: float


class RetrievedPassage(BaseModel):
    chunk_id: UUID
    document_id: UUID
    chunk_index: int
    text: str
    page: str | None = None
    section: str | None = None
    fusion_score: float = 0.0
    rerank_score: float | None = None
    ticker: str
    company_name: str | None = None
    form: str
    filing_date: date
    fiscal_year: int | None = None
    accession_number: str
    neighbors: list["RetrievedPassage"] = Field(default_factory=list)


class SearchFilters(BaseModel):
    document_ids: list[UUID] | None = None
    tickers: list[str] | None = None
