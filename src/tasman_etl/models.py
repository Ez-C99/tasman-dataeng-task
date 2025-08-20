from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

# ---- Pydantic config notes ----
# - Strip whitespace, ignore unknown fields (forward-compatible),
#   use coercion where sensible. Apply stricter rules selectively.
_BASE_CONFIG = ConfigDict(extra="ignore", str_strip_whitespace=True)

# ------------------------------
# RAW API SHAPES (subset)
# ------------------------------


class ApiPositionLocation(BaseModel):
    """
    Represents a job location from the API.
    """

    model_config = _BASE_CONFIG
    LocationName: str | None = None
    CountryCode: str | None = None
    CountrySubDivisionCode: str | None = None
    CityName: str | None = None
    Longitude: float | None = None
    Latitude: float | None = None


class ApiJobCategory(BaseModel):
    """
    Represents a job category from the API.
    """

    model_config = _BASE_CONFIG
    Name: str | None = None
    Code: str


class ApiJobGrade(BaseModel):
    """
    Represents a job grade from the API.
    """

    model_config = _BASE_CONFIG
    Code: str


class ApiPositionRemuneration(BaseModel):
    """
    Represents a job's remuneration details from the API.
    """

    model_config = _BASE_CONFIG
    MinimumRange: int | None = None
    MaximumRange: int | None = None
    RateIntervalCode: str | None = None
    Description: str | None = None

    @field_validator("MinimumRange", "MaximumRange", mode="before")
    @classmethod
    def _strip_currency(cls, v: Any) -> Any:
        """
        Strip currency symbols and commas from the input string.

        :param v: The input string to process.
        :return: The processed string without currency symbols and commas.
        """
        # Examples: "120,000.00", "$95,000", "95000"
        if v is None:
            return None
        s = str(v).replace("$", "").replace(",", "").strip()
        return s or None

    @field_validator("MinimumRange", "MaximumRange", mode="after")
    @classmethod
    def _to_int(cls, v: int | str | None) -> int | None:
        """
        Ensure the value is an integer (after currency stripping).
        """
        if v is None:
            return None
        if isinstance(v, int):
            return v
        try:
            return int(float(v))
        except ValueError as e:
            logging.error(f"Error converting pay range to int: {e}")
            raise
