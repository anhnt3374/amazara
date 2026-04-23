from sqlalchemy.orm import Session

from app.crud.product import get_product_by_id
from app.services.embedding.builders import build_product_embedding_document
from app.services.embedding.contracts import EmbeddingDocument, IndexJob, IndexReason
from app.services.embedding.index_jobs import enqueue_product_index


class ProductEmbeddingService:
    def build_product_document(
        self,
        db: Session,
        product_id: str,
    ) -> EmbeddingDocument:
        product = get_product_by_id(db, product_id)
        if not product:
            raise ValueError("Product not found")
        return build_product_embedding_document(product)

    def enqueue_upsert(self, product_id: str, reason: IndexReason) -> IndexJob:
        return enqueue_product_index(product_id, reason)

    def enqueue_delete(self, product_id: str) -> IndexJob:
        return enqueue_product_index(product_id, IndexReason.PRODUCT_DELETED)
