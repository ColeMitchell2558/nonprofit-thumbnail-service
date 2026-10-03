from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class AssetKind(StrEnum):
    DONOR_RECEIPT = "donor_receipt"
    VOLUNTEER_REMINDER = "volunteer_reminder"
    CAMPAIGN_REPORT = "campaign_report"


class ThumbnailRequest(BaseModel):
    image: dict[str, str]
    asset_kind: AssetKind


class ThumbnailResult(BaseModel):
    asset_kind: AssetKind
    width: int
    height: int
    fit: str
    image: dict[str, Any]
