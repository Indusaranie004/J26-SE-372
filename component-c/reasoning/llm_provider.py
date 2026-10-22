
"""
Base LLM provider interface for Component C.

Allows different language models to be used without
modifying the contextual reasoning pipeline.
"""

from abc import ABC, abstractmethod

from reasoning.output_models import ReasoningResponse


class LLMProvider(ABC):
    """
    Abstract interface for LLM implementations.

    Future implementations:
        - OpenAIProvider
        - GeminiProvider
        - MistralProvider
    """

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> str:
        """
        Generate a structured legal reasoning response.

        Returns:
            A JSON string representing ReasoningResponse.
        """
        pass


def parse_reasoning_output(
    raw_output: str
) -> ReasoningResponse:
    """
    Validate an LLM's JSON response using Pydantic.
    """

    return ReasoningResponse.model_validate_json(raw_output)
