from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, computed_field, field_validator

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
        """
        Convert "yes"/"no" strings to boolean values.

        :param v: The input value to process.
        :return: The processed boolean value or None.
        """
        if isinstance(v, bool) or v is None:
            return v
        s = str(v).strip().lower()
        if s in {"yes", "y", "true"}:
            return True
        if s in {"no", "n", "false"}:
            return False
        return v  # let Pydantic coerce or error


class ApiMatchedObjectDescriptor(BaseModel):
    """
    Model representing a matched object descriptor in the API.
    """

    model_config = _BASE_CONFIG
    PositionID: str
    PositionTitle: str
    PositionURI: str
    ApplyURI: list[str] | None = None
    PositionLocationDisplay: str | None = None
    PositionLocation: list[ApiPositionLocation] | None = None
    OrganizationName: str | None = None
    DepartmentName: str | None = None
    JobCategory: list[ApiJobCategory] | None = None
    JobGrade: list[ApiJobGrade] | None = None
    PositionSchedule: list[dict] | None = None
    PositionOfferingType: list[dict] | None = None
    QualificationSummary: str | None = None
    PositionRemuneration: list[ApiPositionRemuneration] | None = None
    PositionStartDate: datetime | None = None
    PositionEndDate: datetime | None = None
    PublicationStartDate: datetime | None = None
    ApplicationCloseDate: datetime | None = None
    UserArea: dict | None = None  # Details nested under UserArea

    @computed_field
    def details(self) -> ApiDetails | None:
        """
        Get the details from the UserArea.

        :return: The details from the UserArea or None.
        """
        # Only validate if present and is a dict
        if not self.UserArea:
            return None
        d = self.UserArea.get("Details")
        return ApiDetails.model_validate(d) if isinstance(d, dict) else None


class ApiSearchResultItem(BaseModel):
    """
    Model representing a singular search result item in the API.
    """

    model_config = _BASE_CONFIG
    MatchedObjectId: str | None = None
    MatchedObjectDescriptor: ApiMatchedObjectDescriptor


class ApiSearchResult(BaseModel):
    """
    Model representing a search result in the API.
    """

    model_config = _BASE_CONFIG
    SearchResultCount: int
    SearchResultCountAll: int
    SearchResultItems: list[ApiSearchResultItem]


class ApiResponse(BaseModel):
    """
    Model representing a response from the API.
    """

    model_config = _BASE_CONFIG
    LanguageCode: str | None = None
    SearchParameters: dict | None = None
    SearchResult: ApiSearchResult


# ------------------------------
# NORMALISED RECORD DTOs (Silver)
# ------------------------------


class JobRecord(BaseModel):
    """
    Model representing a job record in the system.
    """

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    position_id: str
    matched_object_id: str | None = None
    position_uri: str
    position_title: str
    organization_name: str | None = None
    department_name: str | None = None
    apply_uri: list[str] = Field(default_factory=list)
    position_location_display: str | None = None

    pay_min: int | None = None
    pay_max: int | None = None
    pay_rate_interval_code: str | None = None
    qualification_summary: str | None = None

    publication_start_date: datetime | None = None
    application_close_date: datetime | None = None
    position_start_date: datetime | None = None
    position_end_date: datetime | None = None

    remote_indicator: bool | None = None
    telework_eligible: bool | None = None

    source_event_time: datetime | None = None
    ingest_run_id: str | None = None
    raw_json: dict[str, Any]  # JSONB friendly

    @field_validator("apply_uri", mode="before")
    @classmethod
    def _listify_apply(cls, v: Any) -> list[str]:
        """
        Ensure the apply_uri field is always a list of strings.

        :param v: The value to validate.
        :return: A list of strings.
        """
        if v is None:
            return []
        if isinstance(v, list):
            return [str(x) for x in v]
        return [str(v)]

    @field_validator("pay_max", mode="after")
    @classmethod
    def _min_le_max(cls, v: int | None, info) -> int | None:
        """
        Ensure that pay_min is less than or equal to pay_max.

        :param v: The value of pay_max.
        :param info: The validation info.
        :return: The validated value of pay_max.
        """
        pay_min = info.data.get("pay_min")
        if v is not None and pay_min is not None and pay_min > v:
            raise ValueError("pay_min cannot exceed pay_max")
        return v


class JobDetailsRecord(BaseModel):
    """
    Model representing the details of a job in the system.
    """

    model_config = _BASE_CONFIG
    job_summary: str | None = None
    low_grade: str | None = None
    high_grade: str | None = None
    promotion_potential: str | None = None
    organization_codes: str | None = None
    relocation: str | None = None
    hiring_path: list[str] = Field(default_factory=list)
    mco_tags: list[str] = Field(default_factory=list)
    total_openings: str | None = None
    agency_marketing_statement: str | None = None
    travel_code: str | None = None
    apply_online_url: str | None = None
    detail_status_url: str | None = None
    major_duties: str | None = None
    education: str | None = None
    requirements: str | None = None
    evaluations: str | None = None
    how_to_apply: str | None = None
    what_to_expect_next: str | None = None
    required_documents: str | None = None
    benefits: str | None = None
    benefits_url: str | None = None
    benefits_display_default_text: bool | None = None
    other_information: str | None = None
    key_requirements: list[str] = Field(default_factory=list)
    within_area: str | None = None
    commute_distance: str | None = None
    service_type: str | None = None
    announcement_closing_type: str | None = None
    agency_contact_email: str | None = None
    security_clearance: str | None = None
    drug_test_required: bool | None = None
    position_sensitivity: str | None = None
    adjudication_type: list[str] = Field(default_factory=list)
    financial_disclosure: bool | None = None
    bargaining_unit_status: bool | None = None
