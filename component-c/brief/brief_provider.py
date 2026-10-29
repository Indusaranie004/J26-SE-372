
"""
Component C - Function 2
Gemini Legal Brief Provider

Uses Gemini structured JSON generation for
the LegalBrief output model.

Reuses the Function 1 LLM provider interface
without modifying Function 1.
"""

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from reasoning.llm_provider import LLMProvider
from reasoning.gemini_provider import (
    make_gemini_compatible_schema
)

from brief.output_models import LegalBrief


def prepare_brief_schema():
    """
    Prepare the LegalBrief JSON schema.

    Remove selected schema keywords that may
    cause compatibility issues in Gemini.

    Pydantic performs local validation of
    the generated response afterward.
    """

    json_schema = LegalBrief.model_json_schema()

    compatible_schema = make_gemini_compatible_schema(
        json_schema
    )

    def remove_array_constraints(value):
        if isinstance(value, dict):
            return {
                key: remove_array_constraints(item)
                for key, item in value.items()
                if key not in {"minItems", "maxItems"}
            }

        if isinstance(value, list):
            return [
                remove_array_constraints(item)
                for item in value
            ]

        return value

    return remove_array_constraints(compatible_schema)


class GeminiBriefProvider(LLMProvider):
    """
    Generates structured legal research briefs
    using the configured Gemini model.
    """

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
        Generate a structured legal brief as JSON.
        """

        json_schema = prepare_brief_schema()

        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_json_schema=json_schema
            )
        )

        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty legal brief response."
            )

        return response.text
