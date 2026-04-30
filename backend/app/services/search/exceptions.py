class SemanticSearchError(Exception):
    """Base class for all semantic-search runtime errors."""


class EmbedderUnavailable(SemanticSearchError):
    """Raised when an embedder fails to load or run."""


class VectorStoreUnavailable(SemanticSearchError):
    """Raised when the vector store is unreachable or returns an unrecoverable error."""


class CacheUnavailable(SemanticSearchError):
    """Raised internally when a cache backend is unreachable.

    Caught by the search service and treated as a cache miss; never
    propagated to API callers.
    """
