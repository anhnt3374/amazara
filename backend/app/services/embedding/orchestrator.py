from collections import defaultdict

from app.services.embedding.contracts import AggregatedSearchHit, QueryHit, QueryRequest


def merge_query_hits(hits: list[QueryHit]) -> list[AggregatedSearchHit]:
    grouped: dict[str, list[QueryHit]] = defaultdict(list)
    for hit in hits:
        grouped[hit.product_id].append(hit)

    merged: list[AggregatedSearchHit] = []
    for product_id, evidence in grouped.items():
        ordered_evidence = sorted(evidence, key=lambda hit: hit.score, reverse=True)
        merged.append(
            AggregatedSearchHit(
                product_id=product_id,
                score=sum(hit.score for hit in evidence),
                evidence=ordered_evidence,
            )
        )

    return sorted(merged, key=lambda hit: hit.score, reverse=True)


class SemanticSearchOrchestrator:
    def __init__(self, query_backends: dict[str, object]):
        self.query_backends = query_backends

    def query(self, request: QueryRequest) -> list[AggregatedSearchHit]:
        all_hits: list[QueryHit] = []
        provider_keys = request.provider_keys or list(self.query_backends.keys())
        for provider_key in provider_keys:
            backend = self.query_backends.get(provider_key)
            if backend is None:
                continue
            hits = backend.query(request)
            all_hits.extend(hits)
        return merge_query_hits(all_hits)
