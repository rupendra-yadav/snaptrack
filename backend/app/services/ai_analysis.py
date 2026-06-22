import logging
from app.schemas.meal import AnalysisResult
from app.services.ai.base import AbstractAIProvider, AIProviderError
from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_provider() -> AbstractAIProvider:
    """
    Factory function: returns the configured AI provider.

    To add a new provider:
      1. Add a new AI_PROVIDER option in config.py (e.g. "gemini")
      2. Import and return the new provider class here.
      3. Nothing else changes.
    """
    provider = settings.AI_PROVIDER.lower()

    if provider == "openai":
        from app.services.ai.openai_provider import OpenAIProvider
        return OpenAIProvider()

    raise AIProviderError(
        f"Unknown AI provider: '{provider}'. "
        f"Set AI_PROVIDER=openai in your .env file."
    )


class AIAnalysisService:
    """
    Provider-agnostic meal analysis service.

    The route calls this — it never knows which AI provider is running underneath.
    Accepts raw image bytes + mime type, returns a structured AnalysisResult.
    """

    def __init__(self):
        self.provider = _get_provider()

    async def analyze(self, image_bytes: bytes, mime_type: str) -> AnalysisResult:
        """
        Analyze a meal image and return structured nutrition data.

        Raises:
            AIProviderError: propagated from the provider if the call fails.
        """
        logger.info(f"Running analysis via provider: {settings.AI_PROVIDER}")
        return await self.provider.analyze_image(image_bytes, mime_type)
