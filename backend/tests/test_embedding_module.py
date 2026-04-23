import unittest

import app.db.base  # noqa: F401
from app.models.brand import Brand
from app.models.category import Category
from app.models.product import Product
from app.models.store import Store
from app.services.embedding.builders import build_product_embedding_document
from app.services.embedding.contracts import IndexReason, QueryHit
from app.services.embedding.ingestion_hooks import (
    enqueue_product_created,
    enqueue_product_deleted,
    enqueue_product_updated,
)
from app.services.embedding.milvus_adapter import build_collection_name
from app.services.embedding.orchestrator import merge_query_hits
from app.services.embedding.registry import build_default_registry


class ProductEmbeddingDocumentBuilderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.brand = Brand(name="Cloud Runner")
        self.category = Category(name="Running", brand=self.brand)
        self.store = Store(
            name="Velocity Store",
            slug="velocity-store",
            email="store@example.com",
            password_hash="hashed-password",
        )
        self.product = Product(
            id="product-123",
            name="Daily Trainer",
            description="Breathable shoes for daily road running.",
            price=230000,
            discount=15,
            stock=12,
            image="https://cdn.example.com/a.jpg | https://cdn.example.com/b.jpg",
            category=self.category,
            store=self.store,
        )

    def test_build_product_document_keeps_description_images_and_metadata(self) -> None:
        document = build_product_embedding_document(self.product)

        self.assertEqual(document.product_id, "product-123")
        self.assertEqual(
            document.description_text,
            "Breathable shoes for daily road running.",
        )
        self.assertEqual(
            document.image_urls,
            [
                "https://cdn.example.com/a.jpg",
                "https://cdn.example.com/b.jpg",
            ],
        )
        self.assertEqual(document.metadata["name"], "Daily Trainer")
        self.assertEqual(document.metadata["brand_name"], "Cloud Runner")
        self.assertEqual(document.metadata["category_name"], "Running")
        self.assertEqual(document.metadata["store_name"], "Velocity Store")
        self.assertEqual(document.metadata["discount"], 15)

    def test_build_product_document_handles_missing_optional_fields(self) -> None:
        product = Product(
            id="product-456",
            name="Studio Tee",
            description=None,
            price=99000,
            discount=0,
            stock=6,
            image=None,
            category=None,
            store=self.store,
        )

        document = build_product_embedding_document(product)

        self.assertEqual(document.description_text, "")
        self.assertEqual(document.image_urls, [])
        self.assertIsNone(document.metadata["brand_name"])
        self.assertIsNone(document.metadata["category_name"])


class EmbeddingRegistryTest(unittest.TestCase):
    def test_default_registry_exposes_both_embedding_spaces(self) -> None:
        registry = build_default_registry()

        self.assertEqual(
            set(registry.provider_keys()),
            {"qwen_text", "fg_clip_image"},
        )

        qwen = registry.get("qwen_text")
        self.assertEqual(qwen.provider_key, "qwen_text")
        self.assertEqual(qwen.input_type, "text")
        self.assertTrue(qwen.supports_text_query)

        fg_clip = registry.get("fg_clip_image")
        self.assertEqual(fg_clip.provider_key, "fg_clip_image")
        self.assertEqual(fg_clip.input_type, "image")
        self.assertTrue(fg_clip.supports_text_query)


class QueryAggregationTest(unittest.TestCase):
    def test_merge_query_hits_groups_results_by_product_and_preserves_evidence(self) -> None:
        hits = [
            QueryHit(
                product_id="product-123",
                provider_key="qwen_text",
                record_id="product-123::description",
                score=0.82,
                metadata={"matched_field": "description"},
            ),
            QueryHit(
                product_id="product-123",
                provider_key="fg_clip_image",
                record_id="product-123::image::0",
                score=0.91,
                metadata={"image_index": 0},
            ),
            QueryHit(
                product_id="product-456",
                provider_key="qwen_text",
                record_id="product-456::description",
                score=0.75,
                metadata={"matched_field": "description"},
            ),
        ]

        merged = merge_query_hits(hits)

        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0].product_id, "product-123")
        self.assertAlmostEqual(merged[0].score, 1.73)
        self.assertEqual(
            [e.provider_key for e in merged[0].evidence],
            ["fg_clip_image", "qwen_text"],
        )
        self.assertEqual(merged[1].product_id, "product-456")


class IndexLifecycleHookTest(unittest.TestCase):
    def test_async_hooks_enqueue_product_lifecycle_jobs(self) -> None:
        created = enqueue_product_created("product-123")
        updated = enqueue_product_updated("product-123")
        deleted = enqueue_product_deleted("product-123")

        self.assertEqual(created.product_id, "product-123")
        self.assertEqual(created.reason, IndexReason.PRODUCT_CREATED)
        self.assertEqual(updated.reason, IndexReason.PRODUCT_UPDATED)
        self.assertEqual(deleted.reason, IndexReason.PRODUCT_DELETED)
        self.assertTrue(created.run_async)
        self.assertTrue(updated.run_async)
        self.assertTrue(deleted.run_async)


class MilvusCollectionNamingTest(unittest.TestCase):
    def test_build_collection_name_uses_prefix_and_provider_key(self) -> None:
        self.assertEqual(
            build_collection_name("shope", "qwen_text"),
            "shope_qwen_text",
        )
        self.assertEqual(
            build_collection_name("shope", "fg_clip_image"),
            "shope_fg_clip_image",
        )


if __name__ == "__main__":
    unittest.main()
