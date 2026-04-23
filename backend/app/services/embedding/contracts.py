from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class IndexReason(StrEnum):
    PRODUCT_CREATED = "product_created"
    PRODUCT_UPDATED = "product_updated"
    PRODUCT_DELETED = "product_deleted"
    BACKFILL = "backfill"
    MANUAL = "manual"


@dataclass(slots=True)
class EmbeddingDocument:
    product_id: str
    description_text: str
    image_urls: list[str]
    metadata: dict[str, Any]


@dataclass(slots=True)
class ProviderSpec:
    provider_key: str
    model_id: str
    input_type: str
    supports_text_query: bool
    enabled: bool = True


@dataclass(slots=True)
class VectorRecord:
    provider_key: str
    record_id: str
    product_id: str
    vector: list[float]
    metadata: dict[str, Any]


@dataclass(slots=True)
class QueryRequest:
    query_text: str
    top_k: int = 20
    provider_keys: list[str] | None = None


@dataclass(slots=True)
class QueryHit:
    product_id: str
    provider_key: str
    record_id: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AggregatedSearchHit:
    product_id: str
    score: float
    evidence: list[QueryHit]


@dataclass(slots=True)
class IndexJob:
    product_id: str | None
    reason: IndexReason
    run_async: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
