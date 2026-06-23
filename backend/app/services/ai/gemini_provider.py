import json
import logging
import google.generativeai as genai
from app.core.config import settings
from app.schemas.meal import AnalysisResult, FoodItemBase
from app.services.ai.base import AbstractAIProvider, AIProviderError

logger = logging.getLogger(__name__)

PROMPT = """You are a professional nutritionist. Analyze this meal photo.

Identify every visible food item and estimate:
- Weight in grams
- Calories
- Protein in grams

Rules:
- Identify ALL visible items including sauces, drinks, sides
- Use realistic portion sizes based on visual cues
- Return ONLY valid JSON, no markdown, no explanation

Output format (strict JSON):
{
  "foods": [
    {
      "name": "Food name",
      "estimated_weight_g": 150,
      "calories": 200,
      "protein_g": 12.5
    }
  ],
  "total_calories": 200,
  "total_protein": 12.5
}

All numeric values must be numbers not strings.
total_calories and total_protein must equal the sum of all food items."""


class GeminiProvider(AbstractAIProvider):
    """
    Google Gemini vision implementation of AbstractAIProvider.
    Uses gemini-1.5-flash which is free tier eligible.
    """

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise AIProviderError(
                "GEMINI_API_KEY is not set. Add it to your .env file."
            )
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.AI_MODEL)

    async def analyze_image(self, image_bytes: bytes, mime_type: str) -> AnalysisResult:
        """
        Send image to Gemini and parse the structured response.
        google-generativeai's generate_content is synchronous —
        we call it directly (acceptable for MVP single-user use).
        """
        logger.info(f"Sending image to Gemini ({len(image_bytes) / 1024:.1f} KB)")

        image_part = {"mime_type": mime_type, "data": image_bytes}

        try:
            response = self.model.generate_content(
                [PROMPT, image_part],
                generation_config={"temperature": 0.1},  # low temp = more consistent output
            )
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise AIProviderError(f"Gemini API call failed: {e}") from e

        raw = response.text or ""
        logger.debug(f"Raw Gemini response: {raw}")
        return self._parse_response(raw)

    def _parse_response(self, raw: str) -> AnalysisResult:
        # Strip markdown fences if present
        clean = raw.strip()
        if clean.startswith("```"):
            lines = clean.split("\n")
            clean = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        try:
            data = json.loads(clean)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response: {raw}")
            raise AIProviderError(f"Gemini returned invalid JSON: {e}") from e

        if "foods" not in data:
            raise AIProviderError("Gemini response missing 'foods' key.")

        try:
            foods = [
                FoodItemBase(
                    name=item.get("name", "Unknown"),
                    estimated_weight_g=item.get("estimated_weight_g"),
                    calories=float(item.get("calories", 0)),
                    protein_g=float(item.get("protein_g", 0)),
                )
                for item in data["foods"]
            ]
        except Exception as e:
            raise AIProviderError(f"Failed to parse food items: {e}") from e

        total_calories = round(sum(f.calories for f in foods), 1)
        total_protein = round(sum(f.protein_g for f in foods), 1)

        logger.info(f"Analysis complete: {len(foods)} items, {total_calories} cal, {total_protein}g protein")

        return AnalysisResult(
            foods=foods,
            total_calories=total_calories,
            total_protein=total_protein,
            image_path="",
        )
