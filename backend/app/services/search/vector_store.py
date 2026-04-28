from __future__ import annotations

import logging

import numpy as np
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)

from app.core.config import settings
from app.services.search.exceptions import VectorStoreUnavailable

logger = logging.getLogger(__name__)

_CONNECTION_ALIAS = "default"


def connect() -> None:
    """Idempotently connect to Milvus using settings."""
    if connections.has_connection(_CONNECTION_ALIAS):
        return
    try:
        connections.connect(
            alias=_CONNECTION_ALIAS,
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
        )
    except Exception as e:  # noqa: BLE001
        raise VectorStoreUnavailable(f"connect failed: {e}") from e


def _image_schema() -> CollectionSchema:
    return CollectionSchema(
        fields=[
            FieldSchema("id", DataType.VARCHAR, is_primary=True, max_length=64),
            FieldSchema("product_id", DataType.VARCHAR, max_length=36),
            FieldSchema("category_id", DataType.VARCHAR, max_length=36, nullable=True),
            FieldSchema("brand_id", DataType.VARCHAR, max_length=36, nullable=True),
            FieldSchema("image_idx", DataType.INT8),
            FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=settings.SEMANTIC_FGCLIP_DIM),
        ],
        description="One row per product image",
    )


def _text_schema() -> CollectionSchema:
    return CollectionSchema(
        fields=[
            FieldSchema("id", DataType.VARCHAR, is_primary=True, max_length=36),
            FieldSchema("category_id", DataType.VARCHAR, max_length=36, nullable=True),
            FieldSchema("brand_id", DataType.VARCHAR, max_length=36, nullable=True),
            FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=settings.SEMANTIC_TEXT_DIM),
        ],
        description="One row per product description",
    )


def _index_params() -> dict:
    return {
        "index_type": settings.SEMANTIC_MILVUS_INDEX_TYPE,
        "metric_type": "IP",
        "params": {"nlist": settings.SEMANTIC_MILVUS_NLIST},
    }


def ensure_collections(*, drop: bool = False) -> tuple[Collection, Collection]:
    connect()

    image_name = settings.SEMANTIC_COLLECTION_IMAGE
    text_name = settings.SEMANTIC_COLLECTION_TEXT

    if drop:
        for name in (image_name, text_name):
            if utility.has_collection(name):
                utility.drop_collection(name)

    if not utility.has_collection(image_name):
        coll = Collection(image_name, schema=_image_schema())
        coll.create_index(field_name="embedding", index_params=_index_params())
    if not utility.has_collection(text_name):
        coll = Collection(text_name, schema=_text_schema())
        coll.create_index(field_name="embedding", index_params=_index_params())

    image_coll = Collection(image_name)
    text_coll = Collection(text_name)
    image_coll.load()
    text_coll.load()
    return image_coll, text_coll


def upsert_image_rows(
    coll: Collection,
    rows: list[dict],
) -> None:
    """rows: list of {id, product_id, category_id, brand_id, image_idx, embedding}."""
    if not rows:
        return
    try:
        coll.upsert(rows)
    except Exception as e:  # noqa: BLE001
        raise VectorStoreUnavailable(f"image upsert failed: {e}") from e


def upsert_text_rows(
    coll: Collection,
    rows: list[dict],
) -> None:
    if not rows:
        return
    try:
        coll.upsert(rows)
    except Exception as e:  # noqa: BLE001
        raise VectorStoreUnavailable(f"text upsert failed: {e}") from e


def flush(coll: Collection) -> None:
    coll.flush()


def search_image(
    coll: Collection,
    query: np.ndarray,
    top_k: int,
    expr: str | None,
) -> list[tuple[str, str, float]]:
    """Return list of (image_id, product_id, score) sorted by score desc."""
    try:
        results = coll.search(
            data=[query.tolist()],
            anns_field="embedding",
            param={"metric_type": "IP", "params": {"nprobe": settings.SEMANTIC_MILVUS_NPROBE}},
            limit=top_k,
            expr=expr,
            output_fields=["product_id"],
        )
    except Exception as e:  # noqa: BLE001
        raise VectorStoreUnavailable(f"image search failed: {e}") from e

    out: list[tuple[str, str, float]] = []
    for hit in results[0]:
        out.append((hit.id, hit.entity.get("product_id"), float(hit.score)))
    return out


def search_text(
    coll: Collection,
    query: np.ndarray,
    top_k: int,
    expr: str | None,
) -> list[tuple[str, float]]:
    """Return list of (product_id, score) sorted by score desc."""
    try:
        results = coll.search(
            data=[query.tolist()],
            anns_field="embedding",
            param={"metric_type": "IP", "params": {"nprobe": settings.SEMANTIC_MILVUS_NPROBE}},
            limit=top_k,
            expr=expr,
        )
    except Exception as e:  # noqa: BLE001
        raise VectorStoreUnavailable(f"text search failed: {e}") from e

    return [(hit.id, float(hit.score)) for hit in results[0]]


def build_filter_expr(
    *, category_ids: list[str] | None, brand_ids: list[str] | None
) -> str | None:
    """Return a Milvus boolean expression or None.

    `brand_ids` here refers to the *resolved* brand_id list to filter on; the
    caller must have already converted brand_ids → category_ids if needed.
    """
    parts: list[str] = []
    if category_ids:
        ids = ", ".join(f'"{c}"' for c in category_ids)
        parts.append(f"category_id in [{ids}]")
    if brand_ids:
        ids = ", ".join(f'"{b}"' for b in brand_ids)
        parts.append(f"brand_id in [{ids}]")
    if not parts:
        return None
    return " and ".join(parts)
