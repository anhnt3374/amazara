---
feature: embedding
doc_type: overview
tags: [embedding, semantic-search, milvus, qwen, fg-clip]
---

# Embedding — Overview

## Purpose

The embedding module prepares the backend for future semantic product search without changing the current keyword search flow.

It introduces a shared contract for:

- building one logical embedding document per product
- generating vectors for multiple embedding spaces
- storing and querying vectors through a Milvus-ready adapter
- enqueueing async indexing work for future product create/update/delete flows

## Current Scope

The module lives under `backend/app/services/embedding/`.

Supported embedding spaces:

- `qwen_text` — `Qwen/Qwen3-Embedding-0.6B` for product `description`
- `fg_clip_image` — `qihoo360/fg-clip2-base` for product images, one vector per image

Current search endpoints still use keyword search in `backend/app/crud/product.py`.

## Product Document Contract

Each product is treated as one logical document.

- Embedded text: `description`
- Embedded images: every parsed image URL from `Product.image`
- Metadata only: `name`, `brand`, `category`, `store`, `price`, `discount`, `stock`

The builder entrypoint is `build_product_embedding_document(product)`.

## Query and Indexing Shape

The orchestration layer is prepared for future fan-out search:

- send a text query to one or more enabled embedding spaces
- merge hits by `product_id`
- retain per-space evidence for later ranking/debugging

Indexing is async-first by default:

- product created
- product updated
- product deleted

These lifecycle hooks exist now as enqueue contracts so a future store product management flow can trigger reindexing without redesigning the module.

## Key Files

- `backend/app/services/embedding/contracts.py`
- `backend/app/services/embedding/builders.py`
- `backend/app/services/embedding/registry.py`
- `backend/app/services/embedding/orchestrator.py`
- `backend/app/services/embedding/milvus_adapter.py`
- `backend/app/services/embedding/ingestion_hooks.py`
- `backend/app/services/embedding/product_embedding_service.py`

## Configuration

Embedding-related settings are defined in `backend/app/core/config.py`.

Important settings:

- `EMBEDDING_QWEN_MODEL_ID`
- `EMBEDDING_FG_CLIP_MODEL_ID`
- `EMBEDDING_COLLECTION_PREFIX`
- `EMBEDDING_MILVUS_URI`
- `EMBEDDING_QUERY_TOP_K`
- `EMBEDDING_INDEX_ASYNC`
- `EMBEDDING_BATCH_SIZE`

## Non-Goals

- No current API or frontend search behavior changes
- No store upload/update API yet
- No live Milvus query execution wired into product search yet
