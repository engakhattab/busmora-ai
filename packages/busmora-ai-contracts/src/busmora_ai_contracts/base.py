"""Shared base model and field types for every contract."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


class ContractModel(BaseModel):
    """Base for all contract models.

    ``extra="ignore"`` keeps evolution additive: a worker built against an older
    contract version still accepts a payload that carries newer optional fields.
    """

    model_config = ConfigDict(extra="ignore", frozen=True)


TraceId = Annotated[str, StringConstraints(min_length=1, max_length=128)]
"""Trace identifier started by api-http and carried through every hop (NFR-08)."""

Sha256Hex = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
"""Lower-case hex SHA-256 digest."""

StorageKey = Annotated[str, StringConstraints(min_length=1, max_length=1024)]
"""Object-storage key; always prefixed with the workspace id."""
