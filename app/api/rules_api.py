"""
FX Rules Management API

CRUD operations for managing provider selection and margin adjustment rules.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.services.rules_engine import (
    Rule, RuleType, RulesEngine, get_loader,
    TransactionContext, PricingContext, ProviderContext
)

router = APIRouter(prefix="/api/v1/fx/rules", tags=["rules"])


class RuleListFilter(BaseModel):
    """Query parameters for filtering rules"""
    rule_type: Optional[RuleType] = None
    enabled: Optional[bool] = None
    priority_min: Optional[int] = None
    priority_max: Optional[int] = None


class TestRuleRequest(BaseModel):
    """Request for testing a rule against a context"""
    rule_id: str
    context: Dict[str, Any]


class TestRuleResponse(BaseModel):
    """Response from testing a rule"""
    rule_id: str
    rule_name: str
    matched: bool
    evaluation_time_ms: float
    context: Dict[str, Any]


@router.get("/health")
async def health():
    """Health check for rules engine"""
    engine = RulesEngine()
    loader = get_loader()

    provider_rules = loader.load_rules(RuleType.PROVIDER_SELECTION)
    pricing_rules = loader.load_rules(RuleType.MARGIN_ADJUSTMENT)

    return {
        "status": "healthy",
        "service": "fx-rules-engine",
        "provider_rules_loaded": len(provider_rules),
        "pricing_rules_loaded": len(pricing_rules),
        "total_rules": len(provider_rules) + len(pricing_rules)
    }


@router.get("/", response_model=List[Rule])
async def list_rules(
    rule_type: Optional[str] = None,
    enabled: Optional[bool] = None,
    priority_min: Optional[int] = None,
    priority_max: Optional[int] = None
):
    """
    List all rules with optional filters

    Args:
        rule_type: Filter by rule type (PROVIDER_SELECTION or MARGIN_ADJUSTMENT)
        enabled: Filter by enabled status
        priority_min: Minimum priority
        priority_max: Maximum priority

    Returns:
        List of rules matching filters
    """
    loader = get_loader()

    # Load rules
    if rule_type:
        rules = loader.load_rules(RuleType(rule_type))
    else:
        rules = loader.load_rules()

    # Apply filters
    filtered = rules

    if enabled is not None:
        filtered = [r for r in filtered if r.enabled == enabled]

    if priority_min is not None:
        filtered = [r for r in filtered if r.priority >= priority_min]

    if priority_max is not None:
        filtered = [r for r in filtered if r.priority <= priority_max]

    # Sort by priority descending
    filtered.sort(key=lambda r: r.priority, reverse=True)

    return filtered


@router.get("/{rule_id}", response_model=Rule)
async def get_rule(rule_id: str):
    """
    Get a specific rule by ID

    Args:
        rule_id: Rule identifier

    Returns:
        Rule details
    """
    loader = get_loader()
    all_rules = loader.load_rules()

    for rule in all_rules:
        if rule.rule_id == rule_id:
            return rule

    raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")


@router.post("/", response_model=Rule, status_code=201)
async def create_rule(rule: Rule):
    """
    Create a new rule

    Args:
        rule: Rule to create

    Returns:
        Created rule
    """
    loader = get_loader()

    # Check if rule_id already exists
    existing = loader.load_rules()
    for r in existing:
        if r.rule_id == rule.rule_id:
            raise HTTPException(
                status_code=400,
                detail=f"Rule with ID {rule.rule_id} already exists"
            )

    # Save rule
    success = loader.save_rule(rule)

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to save rule"
        )

    return rule


@router.put("/{rule_id}", response_model=Rule)
async def update_rule(rule_id: str, rule: Rule):
    """
    Update an existing rule

    Args:
        rule_id: ID of rule to update
        rule: Updated rule data

    Returns:
        Updated rule
    """
    if rule_id != rule.rule_id:
        raise HTTPException(
            status_code=400,
            detail="Rule ID in path must match rule ID in body"
        )

    loader = get_loader()

    # Check if rule exists
    existing = loader.load_rules()
    found = False
    for r in existing:
        if r.rule_id == rule_id:
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

    # Update metadata
    rule.metadata.updated_at = datetime.utcnow()

    # Save rule
    success = loader.save_rule(rule)

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to update rule"
        )

    return rule


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(rule_id: str):
    """
    Delete a rule

    Args:
        rule_id: ID of rule to delete
    """
    loader = get_loader()

    success = loader.delete_rule(rule_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Rule {rule_id} not found"
        )

    return None


@router.post("/{rule_id}/toggle", response_model=Rule)
async def toggle_rule(rule_id: str):
    """
    Toggle a rule's enabled status

    Args:
        rule_id: ID of rule to toggle

    Returns:
        Updated rule
    """
    loader = get_loader()

    # Find rule
    all_rules = loader.load_rules()
    rule = None
    for r in all_rules:
        if r.rule_id == rule_id:
            rule = r
            break

    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

    # Toggle enabled
    rule.enabled = not rule.enabled
    rule.metadata.updated_at = datetime.utcnow()

    # Save
    success = loader.save_rule(rule)

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to toggle rule"
        )

    return rule


@router.post("/reload", status_code=200)
async def reload_rules():
    """
    Force reload of rules from configuration files

    Returns:
        Status message with loaded rule counts
    """
    from app.services.rules_engine import reload_rules

    reload_rules()

    loader = get_loader()
    provider_rules = loader.load_rules(RuleType.PROVIDER_SELECTION)
    pricing_rules = loader.load_rules(RuleType.MARGIN_ADJUSTMENT)

    return {
        "status": "reloaded",
        "provider_rules": len(provider_rules),
        "pricing_rules": len(pricing_rules),
        "total_rules": len(provider_rules) + len(pricing_rules),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/validate", status_code=200)
async def validate_rule(rule: Rule):
    """
    Validate a rule without saving it

    Args:
        rule: Rule to validate

    Returns:
        Validation result
    """
    # Basic validation is done by Pydantic model
    # Additional business logic validation can be added here

    errors = []

    # Check priority range
    if rule.priority < 0 or rule.priority > 1000:
        errors.append("Priority must be between 0 and 1000")

    # Check validity period
    if rule.valid_until and rule.valid_until <= rule.valid_from:
        errors.append("valid_until must be after valid_from")

    # Check actions match rule type
    if rule.rule_type == RuleType.PROVIDER_SELECTION:
        if not rule.actions.provider_selection:
            errors.append("Provider selection rule must have provider_selection actions")
    elif rule.rule_type == RuleType.MARGIN_ADJUSTMENT:
        if not rule.actions.margin_adjustment:
            errors.append("Margin adjustment rule must have margin_adjustment actions")

    if errors:
        return {
            "valid": False,
            "errors": errors
        }

    return {
        "valid": True,
        "rule_id": rule.rule_id,
        "rule_name": rule.rule_name
    }


@router.post("/test", response_model=TestRuleResponse)
async def test_rule(request: TestRuleRequest):
    """
    Test a rule against a sample context

    Args:
        request: Test request with rule_id and context

    Returns:
        Test result showing if rule matched
    """
    import time

    # Get rule
    loader = get_loader()
    all_rules = loader.load_rules()
    rule = None
    for r in all_rules:
        if r.rule_id == request.rule_id:
            rule = r
            break

    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

    # Build context from dict
    if rule.rule_type == RuleType.PROVIDER_SELECTION:
        context = ProviderContext(**request.context)
    else:
        context = PricingContext(**request.context)

    # Evaluate
    from app.services.rules_engine import RuleEvaluator
    evaluator = RuleEvaluator()

    start_time = time.time()
    matched = evaluator.evaluate_conditions(rule.conditions, context)
    evaluation_time_ms = (time.time() - start_time) * 1000

    return TestRuleResponse(
        rule_id=rule.rule_id,
        rule_name=rule.rule_name,
        matched=matched,
        evaluation_time_ms=evaluation_time_ms,
        context=request.context
    )


@router.get("/audit/recent", status_code=200)
async def get_recent_audit_logs(limit: int = 100):
    """
    Get recent rule execution audit logs

    Args:
        limit: Maximum number of logs to return (default 100, max 1000)

    Returns:
        Recent audit log entries
    """
    if limit > 1000:
        limit = 1000

    engine = RulesEngine()
    logs = engine.get_audit_logs(limit)

    return {
        "count": len(logs),
        "logs": [log.model_dump() for log in logs]
    }
