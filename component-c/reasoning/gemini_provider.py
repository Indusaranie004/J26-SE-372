
"""
Gemini LLM provider for Component C.

Connects Gemini to the common LLMProvider interface.
"""

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from reasoning.llm_provider import LLMProvider
from reasoning.output_models import ReasoningResponse


def make_gemini_compatible_schema(value):
    """
    Remove JSON Schema keywords that may not be supported
    by Gemini's structured-output configuration.

    Pydantic still validates the final response locally.
    """

    unsupported_keys = {
        "additionalProperties",
        "default",
        "minLength",
        "maxLength"
    }

    if isinstance(value, dict):
        return {
            key: make_gemini_compatible_schema(item)
            for key, item in value.items()
            if key not in unsupported_keys
        }

    if isinstance(value, list):
        return [
            make_gemini_compatible_schema(item)
            for item in value
        ]

    return value


class GeminiProvider(LLMProvider):
    """Generate structured legal reasoning using Gemini."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None
    ):
        load_dotenv()

        key = api_key or os.getenv("GEMINI_API_KEY")

        if not key:
            raise ValueError(
                "GEMINI_API_KEY is missing. Check your .env file."
            )

        self.model = model or os.getenv(
            "GEMINI_MODEL",
            "gemini-3.8-flash"
        )

        self.client = genai.Client(api_key=key)

    def generate(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> str:
        """
        Generate structured legal reasoning as JSON.
        """

        # Convert our Pydantic model into JSON Schema
        json_schema = ReasoningResponse.model_json_schema()

        # Prepare a Gemini-compatible version
        compatible_schema = make_gemini_compatible_schema(
            json_schema
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_json_schema=compatible_schema
            )
        )

        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return response.text
