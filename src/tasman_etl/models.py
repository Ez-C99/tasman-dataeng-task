from __future__ import annotations

import logging
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

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


class ApiDetails(BaseModel):
    """
    USAJOBS 'UserArea.Details' block.
    Accept both the historic typo and the corrected field name for PositionSensitivity.
    """

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    JobSummary: str | None = None
    LowGrade: str | None = None
    HighGrade: str | None = None
    PromotionPotential: str | None = None
    OrganizationCodes: str | None = None
    Relocation: str | None = None
    HiringPath: list[str] | None = None
    MCOTags: list[str] | None = None
    TotalOpenings: str | None = None
    AgencyMarketingStatement: str | None = None
    TravelCode: str | None = None
    ApplyOnlineUrl: str | None = None
    DetailStatusUrl: str | None = None
    MajorDuties: list[str] | None = None
    Education: str | None = None
    Requirements: str | None = None
    Evaluations: str | None = None
    HowToApply: str | None = None
    WhatToExpectNext: str | None = None
    RequiredDocuments: str | None = None
    Benefits: str | None = None
    BenefitsUrl: str | None = None
    BenefitsDisplayDefaultText: bool | None = None
    OtherInformation: str | None = None
    KeyRequirements: list[str] | None = None
    WithinArea: str | None = None
    CommuteDistance: str | None = None
    ServiceType: str | None = None
    AnnouncementClosingType: str | None = None
    AgencyContactEmail: str | None = None
    SecurityClearance: str | None = None
    DrugTestRequired: bool | None = None
    # Accept either "PositionSensitivitiy" (historic typo) or "PositionSensitivity".
    PositionSensitivity: str | None = Field(
        default=None,
        validation_alias=AliasChoices("PositionSensitivitiy", "PositionSensitivity"),
    )
    AdjudicationType: list[str] | None = None
    TeleworkEligible: bool | None = None
    RemoteIndicator: bool | None = None
    FinancialDisclosure: bool | None = None
    BargainingUnitStatus: bool | None = None

    @field_validator(
        "DrugTestRequired",
        "TeleworkEligible",
        "RemoteIndicator",
        "FinancialDisclosure",
        "BenefitsDisplayDefaultText",
        "BargainingUnitStatus",
        mode="before",
    )
    @classmethod
    def _yes_no_to_bool(cls, v: Any) -> bool | None:
        if isinstance(v, bool) or v is None:
            return v
        s = str(v).strip().lower()
        if s in {"yes", "y", "true"}:
            return True
        if s in {"no", "n", "false"}:
            return False
        return v  # let Pydantic coerce or error
