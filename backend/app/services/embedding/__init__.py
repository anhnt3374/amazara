from app.services.embedding.builders import build_product_embedding_document
from app.services.embedding.contracts import (
    AggregatedSearchHit,
    EmbeddingDocument,
    IndexJob,
    IndexReason,
    ProviderSpec,
    QueryHit,
    QueryRequest,
    VectorRecord,
)
from app.services.embedding.index_jobs import enqueue_product_index
from app.services.embedding.orchestrator import (
    SemanticSearchOrchestrator,
    merge_query_hits,
)
from app.services.embedding.product_embedding_service import ProductEmbeddingService
from app.services.embedding.registry import (
    EmbeddingProviderRegistry,
    build_default_registry,
)

__all__ = [
    "AggregatedSearchHit",
    "EmbeddingDocument",
    "EmbeddingProviderRegistry",
    "IndexJob",
    "IndexReason",
    "ProductEmbeddingService",
    "ProviderSpec",
    "QueryHit",
    "QueryRequest",
    "SemanticSearchOrchestrator",
    "VectorRecord",
    "build_default_registry",
    "build_product_embedding_document",
    "enqueue_product_index",
    "merge_query_hits",
]
