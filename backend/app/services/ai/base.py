from abc import ABC, abstractmethod
from app.schemas.meal import AnalysisResult


class AbstractAIProvider(ABC):
    """
    Interface that every AI provider must implement.

    To add a new provider (Gemini, Claude, local model, etc.):
      1. Create a new file in services/ai/
      2. Subclass AbstractAIProvider
      3. Implement analyze_image()
      4. Register it in AIAnalysisService

    Nothing outside this package needs to change.
    """

    @abstractmethod
    async def analyze_image(self, image_bytes: bytes, mime_type: str) -> AnalysisResult:
        """
        Analyze a meal image and return structured nutrition data.

        Args:
            image_bytes: Raw image bytes from the upload.
            mime_type:   MIME type of the image (e.g. "image/jpeg").

        Returns:
            AnalysisResult with detected foods and macro totals.

        Raises:
            AIProviderError: If the provider call fails or returns unparseable data.
        """
        ...


class AIProviderError(Exception):
    """Raised when an AI provider call fails or returns bad data."""
    pass
