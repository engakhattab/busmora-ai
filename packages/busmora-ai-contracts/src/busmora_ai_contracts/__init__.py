"""Canonical contracts for the activities busmora-ai serves over Temporal."""

from importlib.metadata import version

from busmora_ai_contracts.temporal import (
    ACTIVITIES,
    ActivityName,
    ActivitySpec,
    NonRetryableErrorType,
    TaskQueue,
)

__version__ = version("busmora-ai-contracts")

__all__ = [
    "ACTIVITIES",
    "ActivityName",
    "ActivitySpec",
    "NonRetryableErrorType",
    "TaskQueue",
    "__version__",
]
