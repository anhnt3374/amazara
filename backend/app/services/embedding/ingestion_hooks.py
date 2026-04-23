from app.services.embedding.contracts import IndexJob, IndexReason
from app.services.embedding.index_jobs import enqueue_product_index


def enqueue_product_created(product_id: str) -> IndexJob:
    return enqueue_product_index(product_id, IndexReason.PRODUCT_CREATED)


def enqueue_product_updated(product_id: str) -> IndexJob:
    return enqueue_product_index(product_id, IndexReason.PRODUCT_UPDATED)


def enqueue_product_deleted(product_id: str) -> IndexJob:
    return enqueue_product_index(product_id, IndexReason.PRODUCT_DELETED)
