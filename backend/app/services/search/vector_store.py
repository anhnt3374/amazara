from __future__ import annotations

import logging

import numpy as np
import weaviate
from weaviate.classes.config import (
    Configure,
    DataType,
    Property,
    VectorDistances,
)
from weaviate.classes.query import Filter, MetadataQuery
from weaviate.collections import Collection
from weaviate.util import generate_uuid5

from app.core.config import settings
from app.services.search.exceptions import VectorStoreUnavailable

logger = logging.getLogger(__name__)


_client: weaviate.WeaviateClient | None = None


def connect() -> weaviate.WeaviateClient:
    """Idempotently connect to Weaviate using settings."""
    global _client
    if _client is not None and _client.is_connected():
        return _client
    try:
        _client = weaviate.connect_to_local(
            host=settings.WEAVIATE_HOST,
            port=settings.WEAVIATE_HTTP_PORT,
            grpc_port=settings.WEAVIATE_GRPC_PORT,
        )
    except Exception as e:  # noqa: BLE001
        raise VectorStoreUnavailable(f"connect failed: {e}") from e
    return _client


def _hnsw_config():
    return Configure.VectorIndex.hnsw(distance_metric=VectorDistances.COSINE)


def _image_properties() -> list[Property]:
    return [
        Property(name="product_id", data_type=DataType.TEXT),
        Property(name="category_id", data_type=DataType.TEXT),
        Property(name="brand_id", data_type=DataType.TEXT),
        Property(name="image_idx", data_type=DataType.INT),
        Property(name="image_key", data_type=DataType.TEXT),
    ]


def _text_properties() -> list[Property]:
    return [
        Property(name="product_id", data_type=DataType.TEXT),
        Property(name="category_id", data_type=DataType.TEXT),
        Property(name="brand_id", data_type=DataType.TEXT),
    ]


def ensure_collections(*, drop: bool = False) -> tuple[Collection, Collection]:
    client = connect()

    image_name = settings.SEMANTIC_COLLECTION_IMAGE
    text_name = settings.SEMANTIC_COLLECTION_TEXT

    if drop:
        for name in (image_name, text_name):
            if client.collections.exists(name):
                client.collections.delete(name)

    if not client.collections.exists(image_name):
        client.collections.create(
            name=image_name,
            properties=_image_properties(),
            vector_config=Configure.Vectors.self_provided(
                vector_index_config=_hnsw_config(),
            ),
        )
    if not client.collections.exists(text_name):
        client.collections.create(
            name=text_name,
            properties=_text_properties(),
            vector_config=Configure.Vectors.self_provided(
                vector_index_config=_hnsw_config(),
            ),
        )

    return client.collections.get(image_name), client.collections.get(text_name)


def upsert_image_rows(
    coll: Collection,
    rows: list[dict],
) -> None:
    """rows: list of {id, product_id, category_id, brand_id, image_idx, embedding}.

    `id` is the legacy "<product_id>:<image_idx>" string; it is stored as
    `image_key` and used to derive a deterministic UUID5 so that re-runs of
    the indexer upsert in place rather than creating duplicates.
    """
    if not rows:
        return
    try:
        with coll.batch.fixed_size(batch_size=100) as batch:
            for r in rows:
                image_key = r["id"]
                batch.add_object(
                    properties={
                        "product_id": r["product_id"],
                        "category_id": r.get("category_id"),
                        "brand_id": r.get("brand_id"),
                        "image_idx": r["image_idx"],
                        "image_key": image_key,
                    },
                    vector=r["embedding"],
                    uuid=generate_uuid5(image_key),
                )
    except Exception as e:  # noqa: BLE001
        raise VectorStoreUnavailable(f"image upsert failed: {e}") from e


def upsert_text_rows(
    coll: Collection,
    rows: list[dict],
) -> None:
    """rows: list of {id, category_id, brand_id, embedding}, where `id` is the
    product_id. Uses UUID5(product_id) so re-runs upsert in place.
    """
    if not rows:
        return
    try:
        with coll.batch.fixed_size(batch_size=100) as batch:
            for r in rows:
                product_id = r["id"]
                batch.add_object(
                    properties={
                        "product_id": product_id,
                        "category_id": r.get("category_id"),
                        "brand_id": r.get("brand_id"),
                    },
                    vector=r["embedding"],
                    uuid=generate_uuid5(product_id),
                )
    except Exception as e:  # noqa: BLE001
        raise VectorStoreUnavailable(f"text upsert failed: {e}") from e


def flush(coll: Collection) -> None:
    """No-op for Weaviate (writes are persisted automatically)."""
    return None


def search_image(
    coll: Collection,
    query: np.ndarray,
    top_k: int,
    filters: Filter | None,
) -> list[tuple[str, str, float]]:
    """Return list of (image_key, product_id, score) sorted by score desc."""
    try:
        result = coll.query.near_vector(
            near_vector=query.tolist(),
            limit=top_k,
            filters=filters,
            return_properties=["product_id", "image_key"],
            return_metadata=MetadataQuery(distance=True),
        )
    except Exception as e:  # noqa: BLE001
        raise VectorStoreUnavailable(f"image search failed: {e}") from e

    return [
        (
            obj.properties.get("image_key", ""),
            obj.properties["product_id"],
            _score_from_distance(obj.metadata.distance),
        )
        for obj in result.objects
    ]


def search_text(
    coll: Collection,
    query: np.ndarray,
    top_k: int,
    filters: Filter | None,
) -> list[tuple[str, float]]:
    """Return list of (product_id, score) sorted by score desc."""
    try:
        result = coll.query.near_vector(
            near_vector=query.tolist(),
            limit=top_k,
            filters=filters,
            return_properties=["product_id"],
            return_metadata=MetadataQuery(distance=True),
        )
    except Exception as e:  # noqa: BLE001
        raise VectorStoreUnavailable(f"text search failed: {e}") from e

    return [
        (obj.properties["product_id"], _score_from_distance(obj.metadata.distance))
        for obj in result.objects
    ]


def _score_from_distance(distance: float | None) -> float:
    """Convert Weaviate cosine distance to a similarity score.

    Cosine distance in Weaviate ranges 0 (identical) → 2 (opposite); the
    similarity is `1 - distance`. Vectors in this codebase are L2-normalized,
    so this yields the same cosine-similarity range that the previous Milvus
    `IP` metric produced (typically 0..1 for relevant hits).
    """
    if distance is None:
        return 0.0
    return 1.0 - float(distance)


def build_filter_expr(
    *, category_ids: list[str] | None, brand_ids: list[str] | None
) -> Filter | None:
    """Return a Weaviate filter object combining category/brand allow-lists.

    `brand_ids` here is the *resolved* brand_id list to filter on; the caller
    must have already converted brand_ids → category_ids if needed. The
    returned filter is applied as a pre-filter (allow-list) during ANN search.
    """
    parts: list[Filter] = []
    if category_ids:
        parts.append(Filter.by_property("category_id").contains_any(category_ids))
    if brand_ids:
        parts.append(Filter.by_property("brand_id").contains_any(brand_ids))
    if not parts:
        return None
    if len(parts) == 1:
        return parts[0]
    return parts[0] & parts[1]
