import base64
import json
import logging
from openai import AsyncOpenAI
from app.core.config import settings
from app.schemas.meal import AnalysisResult, FoodItemBase
from app.services.ai.base import AbstractAIProvider, AIProviderError

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a professional nutritionist and food analyst.
When given a meal photo, you identify every visible food item and estimate its nutritional content.

Rules:
- Identify ALL visible food items, including sauces, garnishes, and drinks.
- Estimate portion sizes in grams based on visual cues (plate size, typical servings).
- Use standard nutritional databases for calorie and protein estimates.
- If you cannot identify a food, label it "Unknown food item" and estimate conservatively.
- Be realistic — do not over- or under-estimate portions significantly.
- Return ONLY valid JSON. No markdown, no explanation, no code fences.

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

The total_calories and total_protein must equal the sum of all food items.
All numeric values must be numbers, not strings."""

USER_PROMPT = """Analyze this meal photo. Identify all food items, estimate their weight in grams, calories, and protein.
Return strict JSON only."""


class GroqProvider(AbstractAIProvider):
    """
    Groq vision implementation using the OpenAI-compatible API.
    Completely free — no billing required.
    Uses meta-llama/llama-4-scout-17b-16e-instruct which supports image input.
    """

    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise AIProviderError(
                "GROQ_API_KEY is not set. Add it to your .env file."
            )
        # Groq is OpenAI-compatible — just point to a different base_url
        self.client = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
        self.model = settings.AI_MODEL

    async def analyze_image(self, image_bytes: bytes, mime_type: str) -> AnalysisResult:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{mime_type};base64,{b64}"

        logger.info(f"Sending image to Groq/{self.model} ({len(image_bytes) / 1024:.1f} KB)")

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                max_tokens=1000,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": data_url,
                                },
                            },
                            {"type": "text", "text": USER_PROMPT},
                        ],
                    },
                ],
            )
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise AIProviderError(f"Groq API call failed: {e}") from e

        raw = response.choices[0].message.content or ""
        logger.debug(f"Raw Groq response: {raw}")
        return self._parse_response(raw)

    def _parse_response(self, raw: str) -> AnalysisResult:
        clean = raw.strip()
        if clean.startswith("```"):
            lines = clean.split("\n")
            clean = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        try:
            data = json.loads(clean)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Groq response: {raw}")
            raise AIProviderError(f"Groq returned invalid JSON: {e}") from e

        if "foods" not in data:
            raise AIProviderError("Groq response missing 'foods' key.")

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
