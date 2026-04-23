from app.core.config import settings
from app.services.embedding.contracts import ProviderSpec


class FgClipImageProvider:
    provider_key = "fg_clip_image"

    def spec(self) -> ProviderSpec:
        return ProviderSpec(
            provider_key=self.provider_key,
            model_id=settings.EMBEDDING_FG_CLIP_MODEL_ID,
            input_type="image",
            supports_text_query=True,
            enabled=settings.EMBEDDING_FG_CLIP_ENABLED,
        )

    def load_runtime(self) -> object:
        try:
            from PIL import Image
            from transformers import AutoModel, AutoProcessor
        except ImportError as exc:
            raise RuntimeError(
                "transformers and Pillow are required to load the FG-CLIP provider"
            ) from exc
        return {
            "image": Image,
            "processor": AutoProcessor,
            "model": AutoModel,
        }
