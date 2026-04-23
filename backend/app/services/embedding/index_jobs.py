from app.services.embedding.contracts import IndexJob, IndexReason


def enqueue_product_index(
    product_id: str | None,
    reason: IndexReason,
    *,
    run_async: bool = True,
) -> IndexJob:
    return IndexJob(
        product_id=product_id,
        reason=reason,
        run_async=run_async,
    )
