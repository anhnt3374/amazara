from app.services.embedding.contracts import ProviderSpec
from app.services.embedding.providers import FgClipImageProvider, QwenTextProvider


class EmbeddingProviderRegistry:
    def __init__(self, providers: list[ProviderSpec]):
        self._providers = {provider.provider_key: provider for provider in providers}

    def get(self, provider_key: str) -> ProviderSpec:
        try:
            return self._providers[provider_key]
        except KeyError as exc:
            raise KeyError(f"Unknown embedding provider: {provider_key}") from exc

    def provider_keys(self) -> list[str]:
        return list(self._providers.keys())

    def enabled_provider_keys(self) -> list[str]:
        return [
            provider_key
            for provider_key, provider in self._providers.items()
            if provider.enabled
        ]


def build_default_registry() -> EmbeddingProviderRegistry:
    providers = [
        QwenTextProvider().spec(),
        FgClipImageProvider().spec(),
    ]
    return EmbeddingProviderRegistry(providers)
