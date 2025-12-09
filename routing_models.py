"""
Pydantic Models for FX Smart Routing Engine
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum


# =============================================================================
# Enums
# =============================================================================

class RoutingObjective(str, Enum):
    """Routing optimization objectives"""
    BEST_RATE = "BEST_RATE"          # Lowest cost
    OPTIMUM = "OPTIMUM"              # Balanced
    FASTEST_EXECUTION = "FASTEST_EXECUTION"  # Speed priority
    MAX_STP = "MAX_STP"              # Maximum automation


class CustomerTier(str, Enum):
    """Customer tier levels"""
    PLATINUM = "PLATINUM"
    GOLD = "GOLD"
    SILVER = "SILVER"
    BRONZE = "BRONZE"
    RETAIL = "RETAIL"


class ProviderType(str, Enum):
    """FX Provider types"""
    INTERNAL = "INTERNAL"
    LOCAL_BANK = "LOCAL_BANK"
    CORRESPONDENT_BANK = "CORRESPONDENT_BANK"
    FINTECH = "FINTECH"
    FX_DEALER = "FX_DEALER"
    MARKET_DATA = "MARKET_DATA"


class RouteType(str, Enum):
    """Type of routing path"""
    DIRECT = "DIRECT"                # Direct currency pair
    TRIANGULATED = "TRIANGULATED"    # Via bridge currency
    CROSS = "CROSS"                  # Cross rate calculation


class TreasuryPosition(str, Enum):
    """Treasury position status"""
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"


class Direction(str, Enum):
    """Transaction direction"""
    BUY = "BUY"
    SELL = "SELL"


# =============================================================================
# Request Models
# =============================================================================

class CustomerContext(BaseModel):
    """Customer details for routing decisions"""
    customer_id: str = Field(..., description="Unique customer identifier")
    tier: CustomerTier = Field(default=CustomerTier.RETAIL)
    annual_volume_usd: Optional[Decimal] = Field(default=None)
    tenure_years: Optional[int] = Field(default=0)
    preferred_providers: Optional[List[str]] = Field(default=None)
    blocked_providers: Optional[List[str]] = Field(default=None)


class SmartRoutingRequest(BaseModel):
    """Request for smart routing recommendation"""
    source_currency: str = Field(..., min_length=3, max_length=3)
    target_currency: str = Field(..., min_length=3, max_length=3)
    amount: Decimal = Field(..., gt=0)
    direction: Direction = Field(default=Direction.SELL)
    objective: RoutingObjective = Field(default=RoutingObjective.OPTIMUM)
    customer: Optional[CustomerContext] = Field(default=None)
    require_stp: bool = Field(default=False)
    max_settlement_hours: Optional[int] = Field(default=None)
    reference_id: Optional[str] = Field(default=None)


# =============================================================================
# Provider & Rate Models
# =============================================================================

class ProviderRate(BaseModel):
    """Rate from a specific provider"""
    provider_id: str
    provider_name: str
    provider_type: ProviderType
    bid_rate: Decimal
    ask_rate: Decimal
    mid_rate: Decimal
    spread_bps: int
    markup_bps: int
    final_rate: Decimal = Field(..., description="Rate after all adjustments")
    settlement_hours: int
    stp_enabled: bool
    reliability_score: float
    timestamp: datetime
    valid_until: datetime


class RouteLeg(BaseModel):
    """Single leg of a route (for triangulation)"""
    leg_number: int
    source_currency: str
    target_currency: str
    provider_id: str
    rate: Decimal
    amount_in: Decimal
    amount_out: Decimal


class RouteOption(BaseModel):
    """A possible routing option"""
    route_id: str
    route_type: RouteType
    provider_id: str
    provider_name: str
    legs: List[RouteLeg]
    
    # Rate details
    effective_rate: Decimal
    total_spread_bps: int
    total_markup_bps: int
    customer_rate: Decimal = Field(..., description="Final rate for customer")
    
    # Amounts
    source_amount: Decimal
    target_amount: Decimal
    
    # Scores (0-100)
    rate_score: float
    reliability_score: float
    speed_score: float
    stp_score: float
    overall_score: float
    
    # Execution details
    settlement_hours: int
    stp_enabled: bool
    requires_manual_review: bool
    
    # Cost breakdown
    cost_breakdown: Dict[str, Decimal]


# =============================================================================
# Response Models
# =============================================================================

class TreasuryInfo(BaseModel):
    """Treasury position and rate information"""
    treasury_rate: Optional[Decimal] = None
    position: Optional[TreasuryPosition] = None
    exposure_pct: Optional[float] = None
    position_adjustment_bps: Optional[int] = None
    can_execute_internally: bool = False


class TriangulationInfo(BaseModel):
    """Triangulation analysis results"""
    is_triangulated: bool
    bridge_currency: Optional[str] = None
    direct_rate: Optional[Decimal] = None
    triangulated_rate: Optional[Decimal] = None
    savings_bps: Optional[int] = None
    recommended: bool = False


class SmartRoutingResponse(BaseModel):
    """Smart routing recommendation response"""
    request_id: str
    timestamp: datetime
    
    # Request echo
    source_currency: str
    target_currency: str
    amount: Decimal
    direction: Direction
    objective: RoutingObjective
    
    # Customer context applied
    customer_tier: CustomerTier
    customer_discounts_applied: Dict[str, Any]
    
    # Treasury analysis
    treasury: TreasuryInfo
    
    # Triangulation analysis
    triangulation: TriangulationInfo
    
    # Recommended route
    recommended_route: RouteOption
    
    # Alternative routes (sorted by overall_score desc)
    alternative_routes: List[RouteOption]
    
    # Summary
    best_rate: Decimal
    best_rate_provider: str
    fastest_settlement_hours: int
    fastest_provider: str
    
    # Execution guidance
    stp_eligible: bool
    requires_approval: bool
    approval_reason: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class RoutingAnalytics(BaseModel):
    """Analytics for routing decision"""
    providers_considered: int
    providers_eligible: int
    routes_evaluated: int
    triangulation_evaluated: bool
    treasury_rate_available: bool
    execution_time_ms: float
