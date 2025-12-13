"""
Deal Models - Pydantic models for FX Treasury Deals
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class DealStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    FULLY_UTILIZED = "FULLY_UTILIZED"


class DealSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class AuditAction(str, Enum):
    CREATED = "CREATED"
    MODIFIED = "MODIFIED"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    UTILIZED = "UTILIZED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class CustomerTier(str, Enum):
    PLATINUM = "PLATINUM"
    GOLD = "GOLD"
    SILVER = "SILVER"
    BRONZE = "BRONZE"
    RETAIL = "RETAIL"


# Request Models

class CreateDealRequest(BaseModel):
    currency_pair: str = Field(..., description="Currency pair e.g. USDINR")
    side: DealSide = Field(..., description="BUY or SELL from treasury perspective")
    buy_rate: float = Field(..., gt=0, description="Rate treasury buys at")
    sell_rate: float = Field(..., gt=0, description="Rate treasury sells at")
    amount: float = Field(..., gt=0, description="Total deal amount")
    valid_from: datetime = Field(..., description="Start of validity")
    valid_until: datetime = Field(..., description="End of validity")
    customer_tier: Optional[CustomerTier] = Field(None, description="Restrict to specific tier")
    min_amount: float = Field(default=1000, ge=0, description="Minimum transaction size")
    max_amount_per_txn: Optional[float] = Field(None, description="Maximum per transaction")
    notes: Optional[str] = Field(None, description="Internal notes")
    created_by: str = Field(..., description="Treasury user ID")


class UpdateDealRequest(BaseModel):
    buy_rate: Optional[float] = Field(None, gt=0)
    sell_rate: Optional[float] = Field(None, gt=0)
    amount: Optional[float] = Field(None, gt=0)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    customer_tier: Optional[CustomerTier] = None
    min_amount: Optional[float] = Field(None, ge=0)
    max_amount_per_txn: Optional[float] = None
    notes: Optional[str] = None


class SubmitDealRequest(BaseModel):
    submitted_by: str = Field(..., description="User submitting for approval")


class ApproveDealRequest(BaseModel):
    approved_by: str = Field(..., description="Approver user ID")
    comments: Optional[str] = None


class RejectDealRequest(BaseModel):
    rejected_by: str = Field(..., description="Rejector user ID")
    rejection_reason: str = Field(..., description="Reason for rejection")


class UtilizeDealRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to utilize")
    customer_id: str = Field(..., description="Customer identifier")
    customer_tier: CustomerTier = Field(..., description="Customer tier")
    transaction_ref: Optional[str] = Field(None, description="External reference")


class CancelDealRequest(BaseModel):
    cancelled_by: str = Field(..., description="User cancelling the deal")
    cancellation_reason: str = Field(..., description="Reason for cancellation")


# Response Models

class Deal(BaseModel):
    deal_id: str
    currency_pair: str
    side: DealSide
    buy_rate: float
    sell_rate: float
    spread_bps: float
    amount: float
    available_amount: float
    utilized_amount: float
    valid_from: datetime
    valid_until: datetime
    status: DealStatus
    customer_tier: Optional[CustomerTier]
    min_amount: float
    max_amount_per_txn: Optional[float]
    created_by: str
    created_at: datetime
    updated_at: datetime
    submitted_by: Optional[str] = None
    submitted_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    cancelled_by: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    notes: Optional[str] = None


class Utilization(BaseModel):
    utilization_id: str
    deal_id: str
    amount: float
    rate_applied: float
    customer_id: str
    customer_tier: CustomerTier
    transaction_ref: Optional[str]
    utilized_at: datetime


class AuditLogEntry(BaseModel):
    log_id: str
    deal_id: str
    action: AuditAction
    actor: str
    timestamp: datetime
    old_values: Optional[dict] = None
    new_values: Optional[dict] = None
    details: Optional[str] = None


class BestRateResponse(BaseModel):
    currency_pair: str
    side: str
    rate: float
    source: str  # "DEAL" or "TREASURY"
    deal_id: Optional[str] = None
    available_amount: Optional[float] = None
    valid_until: Optional[datetime] = None
    treasury_rate: float
    savings_bps: float


class DealListResponse(BaseModel):
    deals: List[Deal]
    total: int
    page: int
    page_size: int
