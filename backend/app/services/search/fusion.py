def _min_max_normalize(values: dict[str, float]) -> dict[str, float]:
    if not values:
        return {}
    lo = min(values.values())
    hi = max(values.values())
    span = hi - lo
    if span == 0:
        return {k: 0.0 for k in values}
    return {k: (v - lo) / span for k, v in values.items()}


def fuse_and_filter(
    image_scores: dict[str, float],
    text_scores: dict[str, float],
    alpha: float,
    tau: float,
) -> list[tuple[str, float]]:
    """Combine image and text scores into a ranked list, then drop outliers.

    Args:
        image_scores: product_id → image-side score (already aggregated).
        text_scores: product_id → text-side score.
        alpha: weight of image side; text weight = 1 - alpha. In [0, 1].
        tau: keep candidates with final score >= tau * top1_final. In [0, 1].
            tau=0 disables the outlier cut.

    Returns:
        list of (product_id, final_score) sorted by final_score descending.
        Empty list if both inputs are empty.
    """
    candidate_ids = set(image_scores) | set(text_scores)
    if not candidate_ids:
        return []

    img_dict = {pid: image_scores.get(pid, 0.0) for pid in candidate_ids}
    txt_dict = {pid: text_scores.get(pid, 0.0) for pid in candidate_ids}

    img_norm = _min_max_normalize(img_dict)
    txt_norm = _min_max_normalize(txt_dict)

    finals = [
        (pid, alpha * img_norm[pid] + (1.0 - alpha) * txt_norm[pid])
        for pid in candidate_ids
    ]
    finals.sort(key=lambda x: x[1], reverse=True)

    top1 = finals[0][1]
    if top1 <= 0.0 or tau <= 0.0:
        return finals

    cutoff = tau * top1
    return [(pid, score) for pid, score in finals if score >= cutoff]
