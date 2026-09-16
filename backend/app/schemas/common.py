"""Define reusable response envelopes."""

from pydantic import BaseModel, ConfigDict


class ErrorDetail(BaseModel):
    """Describe a machine-readable API error.

    Args:
        BaseModel: Reject unexpected response fields.
    """

    model_config = ConfigDict(extra="forbid")
    code: str
    message: str
    correlation_id: str


class ErrorResponse(BaseModel):
    """Wrap an API error in the shared wire format."""

    model_config = ConfigDict(extra="forbid")
    error: ErrorDetail
