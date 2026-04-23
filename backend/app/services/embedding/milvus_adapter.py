from dataclasses import dataclass
from typing import Any

from app.services.embedding.contracts import QueryHit, QueryRequest, VectorRecord


def build_collection_name(prefix: str, provider_key: str) -> str:
    return f"{prefix}_{provider_key}"


@dataclass(slots=True)
class MilvusSearchRequest:
    collection_name: str
    query_vector: list[float]
    top_k: int
    filters: dict[str, Any] | None = None


class MilvusVectorStore:
    def __init__(self, uri: str, collection_prefix: str):
        self.uri = uri
        self.collection_prefix = collection_prefix

    def _import_client(self):
        try:
            from pymilvus import MilvusClient
        except ImportError as exc:
            raise RuntimeError(
                "pymilvus is required to use the Milvus vector store"
            ) from exc
        return MilvusClient(uri=self.uri)

    def upsert_records(self, provider_key: str, records: list[VectorRecord]) -> dict[str, Any]:
        collection_name = build_collection_name(self.collection_prefix, provider_key)
        payload = [
            {
                "id": record.record_id,
                "product_id": record.product_id,
                "vector": record.vector,
                "metadata": record.metadata,
            }
            for record in records
        ]
        return {
            "collection_name": collection_name,
            "payload": payload,
        }

    def delete_product(self, provider_key: str, product_id: str) -> dict[str, Any]:
        collection_name = build_collection_name(self.collection_prefix, provider_key)
        return {
            "collection_name": collection_name,
            "filter": f'product_id == "{product_id}"',
        }

    def query(
        self,
        provider_key: str,
        request: MilvusSearchRequest,
    ) -> list[QueryHit]:
        _ = provider_key
        _ = request
        return []

