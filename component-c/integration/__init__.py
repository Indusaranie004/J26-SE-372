"""
Component C integration adapters.

This package contains boundary models and adapters used to
normalize upstream component outputs before they enter the
reasoning and legal-brief pipelines.
"""

from integration.component_b_adapter import (
    component_b_to_reasoning_request,
)
from integration.component_b_models import (
    ComponentBReasoningRequest,
)

__all__ = [
    "ComponentBReasoningRequest",
    "component_b_to_reasoning_request",
]