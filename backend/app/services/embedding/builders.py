from app.models.product import Product
from app.services.embedding.contracts import EmbeddingDocument


def _parse_image_urls(raw_image: str | None) -> list[str]:
    if not raw_image:
        return []
    return [part.strip() for part in raw_image.split("|") if part.strip()]


def build_product_embedding_document(product: Product) -> EmbeddingDocument:
    category = product.category
    brand = category.brand if category else None
    store = product.store
    metadata = {
        "product_id": product.id,
        "name": product.name,
        "brand_name": brand.name if brand else None,
        "category_name": category.name if category else None,
        "store_id": product.store_id,
        "store_name": store.name if store else None,
        "price": product.price,
        "discount": product.discount,
        "stock": product.stock,
    }
    return EmbeddingDocument(
        product_id=product.id,
        description_text=(product.description or "").strip(),
        image_urls=_parse_image_urls(product.image),
        metadata=metadata,
    )
