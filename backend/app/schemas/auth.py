"""Define strict authentication request and response contracts."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MobileRequest(BaseModel):
    """Accept an exact ASCII ten-digit mobile number."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    mobile_number: str = Field(min_length=10, max_length=10)

    @field_validator("mobile_number")
    @classmethod
    def validate_mobile_number(cls, value: str) -> str:
        """Reject mobile numbers that are not exactly ten ASCII digits.

        Args:
            value: The trimmed mobile number submitted by the client.

        Returns:
            The validated mobile number.

        Raises:
            ValueError: If the value is malformed.
        """
        if len(value) != 10 or not value.isascii() or not value.isdigit():
            raise ValueError("mobile_number must contain exactly ten ASCII digits")
        return value


class VerifyRequest(MobileRequest):
    """Accept an OTP alongside a valid mobile number."""

    otp: str = Field(min_length=1, max_length=32)


class LoginResponse(BaseModel):
    """Return the required next step for a valid mobile login request."""

    model_config = ConfigDict(extra="forbid")
    authentication_state: Literal["otp_required"]
    mobile_number: str


class VerifyResponse(BaseModel):
    """Return the bearer token and its validated JWT claims."""

    model_config = ConfigDict(extra="forbid")
    access_token: str
    token_type: Literal["bearer"]
    expires_in: int
    claims: dict[str, str | int]
