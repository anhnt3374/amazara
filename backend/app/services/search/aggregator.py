from collections import defaultdict
from collections.abc import Iterable


def aggregate_image_scores(
    rows: Iterable[tuple[str, str, float]],
    top_k: int,
) -> dict[str, float]:
    """Group per-image scores by product_id and reduce via top-K mean.

    Args:
        rows: iterable of (image_id, product_id, score). image_id is unused
            but kept in the row shape because that is what the vector store
            search results provide.
        top_k: number of highest-scoring images to average per product. If a
            product has fewer than top_k images in `rows`, the mean is taken
            over what is available.

    Returns:
        dict mapping product_id to the aggregated score.

    Raises:
        ValueError: if top_k <= 0.
    """
    if top_k <= 0:
        raise ValueError("top_k must be positive")

    groups: dict[str, list[float]] = defaultdict(list)
    for _image_id, product_id, score in rows:
        groups[product_id].append(score)

    aggregated: dict[str, float] = {}
    for product_id, scores in groups.items():
        scores.sort(reverse=True)
        kept = scores[:top_k]
        aggregated[product_id] = sum(kept) / len(kept)
    return aggregated
