
"""
Gemini LLM provider for Component C.

Connects Google's Gemini API to the common
LLMProvider interface used by the reasoning pipeline.
"""

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from reasoning.llm_provider import LLMProvider
from reasoning.output_models import ReasoningResponse


class GeminiProvider(LLMProvider):
    """Generate structured legal reasoning using Gemini."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None
    ):
        load_dotenv()

        # Credentials and model configuration
        key = api_key or os.getenv("GEMINI_API_KEY")

        if not key:
            raise ValueError(
                "GEMINI_API_KEY is missing. Check your .env file."
            )

        self.model = model or os.getenv(
            "GEMINI_MODEL",
            "gemini-3.8-flash"
        )

        # Initialize the Gemini API client
        self.client = genai.Client(api_key=key)

    def generate(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> str:
        """
        Send prompts to Gemini and request structured JSON.

        Args:
            system_prompt: Instructions for legal reasoning.
            user_prompt: Context and evidence to analyze.

        Returns:
            JSON string matching the reasoning output schema.
        """

        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=ReasoningResponse
            )
        )

        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return response.text
