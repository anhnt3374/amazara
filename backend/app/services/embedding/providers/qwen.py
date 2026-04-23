from app.core.config import settings
from app.services.embedding.contracts import ProviderSpec


class QwenTextProvider:
    provider_key = "qwen_text"

    def spec(self) -> ProviderSpec:
        return ProviderSpec(
            provider_key=self.provider_key,
            model_id=settings.EMBEDDING_QWEN_MODEL_ID,
            input_type="text",
            supports_text_query=True,
            enabled=settings.EMBEDDING_QWEN_ENABLED,
        )

    def load_runtime(self) -> object:
        try:
            from transformers import AutoModel, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "transformers is required to load the Qwen embedding provider"
            ) from exc
        return {
            "tokenizer": AutoTokenizer,
            "model": AutoModel,
        }
