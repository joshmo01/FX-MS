"""
Rules Engine Data Models

Pydantic models for rules, conditions, actions, contexts, and evaluation results.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


class RuleType(str, Enum):
    """Types of rules supported by the engine"""
    PROVIDER_SELECTION = "PROVIDER_SELECTION"
    MARGIN_ADJUSTMENT = "MARGIN_ADJUSTMENT"


class ConditionOperator(str, Enum):
    """Logical operators for combining criteria"""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class CriterionOperator(str, Enum):
    """Comparison operators for individual criteria"""
    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    GREATER_THAN = "GREATER_THAN"
    GREATER_THAN_OR_EQUAL = "GREATER_THAN_OR_EQUAL"
    LESS_THAN = "LESS_THAN"
    LESS_THAN_OR_EQUAL = "LESS_THAN_OR_EQUAL"
    IN = "IN"
    NOT_IN = "NOT_IN"
    CONTAINS = "CONTAINS"
    NOT_CONTAINS = "NOT_CONTAINS"
    BETWEEN = "BETWEEN"
    NOT_BETWEEN = "NOT_BETWEEN"
    WITHIN_HOURS = "WITHIN_HOURS"
    OUTSIDE_HOURS = "OUTSIDE_HOURS"
    MATCHES_REGEX = "MATCHES_REGEX"
    STARTS_WITH = "STARTS_WITH"
    ENDS_WITH = "ENDS_WITH"


class Criterion(BaseModel):
    """Individual rule criterion"""
    field: str
    operator: CriterionOperator
    value: Optional[Any] = None
    values: Optional[List[Any]] = None


class RuleConditions(BaseModel):
    """Nested conditions supporting AND/OR/NOT logic"""
    operator: ConditionOperator
    criteria: List[Union[Criterion, 'RuleConditions']]


# Enable self-referencing for nested conditions
RuleConditions.model_rebuild()


class ProviderSelectionAction(BaseModel):
    """Actions for provider selection rules"""
    preferred_providers: Optional[List[str]] = Field(default_factory=list)
    excluded_providers: Optional[List[str]] = Field(default_factory=list)
    routing_objective_override: Optional[str] = None
    force_provider: bool = False


class MarginAdjustmentAction(BaseModel):
    """Actions for margin adjustment rules"""
    base_margin_override: Optional[float] = None
    additional_margin_bps: Optional[float] = None
    tier_adjustment_multiplier: Optional[float] = None
    min_margin_bps: Optional[float] = None
    max_margin_bps: Optional[float] = None


class RuleActions(BaseModel):
    """Combined actions for all rule types"""
    provider_selection: Optional[ProviderSelectionAction] = None
    margin_adjustment: Optional[MarginAdjustmentAction] = None


class RuleMetadata(BaseModel):
    """Metadata for rules"""
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class Rule(BaseModel):
    """Main rule structure"""
    rule_id: str
    rule_name: str
    rule_type: RuleType
    priority: int = Field(ge=0, le=1000)
    enabled: bool = True
    valid_from: datetime
    valid_until: Optional[datetime] = None
    conditions: RuleConditions
    actions: RuleActions
    metadata: RuleMetadata


class TransactionContext(BaseModel):
    """Base context for rule evaluation with extensible custom attributes"""
    # Common fields
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow().replace(tzinfo=None))

    # Customer fields
    customer_id: Optional[str] = None
    customer_segment: Optional[str] = None
    customer_tier: Optional[str] = None
    customer_annual_volume: Optional[float] = None

    # Currency fields
    currency_pair: Optional[str] = None
    base_currency: Optional[str] = None
    quote_currency: Optional[str] = None
    currency_category: Optional[str] = None

    # Transaction fields
    amount: Optional[float] = None
    amount_tier: Optional[str] = None
    direction: Optional[str] = None  # BUY/SELL

    # Location fields
    office: Optional[str] = None
    region: Optional[str] = None

    # Temporal fields
    time_of_day: Optional[str] = None
    day_of_week: Optional[str] = None
    is_holiday: Optional[bool] = None

    # Extensible custom attributes - any additional parameters
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow"  # Allow additional fields


class PricingContext(TransactionContext):
    """Context specific to pricing/margin rules"""
    negotiated_discount_bps: Optional[float] = None
    segment_base_margin: Optional[float] = None
    tier_adjustment: Optional[float] = None
    currency_factor: Optional[float] = None


class ProviderContext(TransactionContext):
    """Context specific to provider selection rules"""
    routing_objective: Optional[str] = None
    available_providers: Optional[List[str]] = None
    provider_type: Optional[str] = None


class RuleEvaluationResult(BaseModel):
    """Result of rule evaluation"""
    matched: bool
    winning_rule: Optional[Rule] = None
    actions: Optional[RuleActions] = None
    alternatives: List[Rule] = Field(default_factory=list)
    evaluation_time_ms: Optional[float] = None
    use_default: bool = False


class RuleAuditLog(BaseModel):
    """Audit log entry for rule application"""
    audit_id: Optional[str] = None
    rule_id: Optional[str] = None
    rule_name: Optional[str] = None
    transaction_id: Optional[str] = None
    context: Dict[str, Any]
    matched: bool
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    execution_time_ms: float
    result: Dict[str, Any] = Field(default_factory=dict)
