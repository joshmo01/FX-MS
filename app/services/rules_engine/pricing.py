"""
Pricing Rule Actions

Handles application of margin adjustment rules to pricing calculations.
"""
from typing import Dict, Optional
import logging

from .models import MarginAdjustmentAction

logger = logging.getLogger(__name__)


def apply_margin_rules(
    actions: MarginAdjustmentAction,
    base_margin: float,
    tier_adjustment: float,
    currency_factor: float,
    negotiated_discount: float = 0
) -> Dict[str, float]:
    """
    Apply margin adjustment rule actions to pricing calculation

    Args:
        actions: Margin adjustment actions from matching rule
        base_margin: Base margin in bps
        tier_adjustment: Tier-based adjustment in bps
        currency_factor: Currency category factor in bps
        negotiated_discount: Negotiated discount in bps

    Returns:
        Dict with adjusted margin components and totals
    """
    result = {
        'base_margin': base_margin,
        'tier_adjustment': tier_adjustment,
        'currency_factor': currency_factor,
        'negotiated_discount': negotiated_discount,
        'additional_margin_bps': 0,
        'tier_multiplier': 1.0,
        'total_before_constraints': 0,
        'total_margin_bps': 0,
        'min_margin_bps': None,
        'max_margin_bps': None
    }

    # Apply base margin override
    if actions.base_margin_override is not None:
        result['base_margin'] = actions.base_margin_override
        logger.debug(f"Base margin overridden to: {actions.base_margin_override} bps")

    # Apply tier adjustment multiplier
    if actions.tier_adjustment_multiplier is not None:
        result['tier_multiplier'] = actions.tier_adjustment_multiplier
        result['tier_adjustment'] = tier_adjustment * actions.tier_adjustment_multiplier
        logger.debug(
            f"Tier adjustment multiplied by {actions.tier_adjustment_multiplier}: "
            f"{tier_adjustment} -> {result['tier_adjustment']} bps"
        )

    # Add additional margin
    if actions.additional_margin_bps is not None:
        result['additional_margin_bps'] = actions.additional_margin_bps
        logger.debug(f"Additional margin added: {actions.additional_margin_bps} bps")

    # Calculate total before constraints
    total_before_constraints = (
        result['base_margin'] +
        result['tier_adjustment'] +
        result['currency_factor'] +
        result['additional_margin_bps'] -
        result['negotiated_discount']
    )
    result['total_before_constraints'] = total_before_constraints

    # Apply min/max constraints
    total_margin = total_before_constraints

    if actions.min_margin_bps is not None:
        result['min_margin_bps'] = actions.min_margin_bps
        if total_margin < actions.min_margin_bps:
            total_margin = actions.min_margin_bps
            logger.debug(f"Margin constrained to minimum: {actions.min_margin_bps} bps")

    if actions.max_margin_bps is not None:
        result['max_margin_bps'] = actions.max_margin_bps
        if total_margin > actions.max_margin_bps:
            total_margin = actions.max_margin_bps
            logger.debug(f"Margin constrained to maximum: {actions.max_margin_bps} bps")

    result['total_margin_bps'] = total_margin

    logger.info(
        f"Margin calculation: base={result['base_margin']}, "
        f"tier={result['tier_adjustment']}, "
        f"currency={result['currency_factor']}, "
        f"additional={result['additional_margin_bps']}, "
        f"discount={result['negotiated_discount']} "
        f"-> total={result['total_margin_bps']} bps"
    )

    return result


def calculate_margin_with_rules(
    actions: Optional[MarginAdjustmentAction],
    base_margin: float,
    tier_adjustment: float,
    currency_factor: float,
    negotiated_discount: float = 0,
    fallback_min: Optional[float] = None,
    fallback_max: Optional[float] = None
) -> float:
    """
    Calculate final margin with or without rule actions

    Args:
        actions: Optional margin adjustment actions (None means no rule matched)
        base_margin: Base margin in bps
        tier_adjustment: Tier-based adjustment in bps
        currency_factor: Currency category factor in bps
        negotiated_discount: Negotiated discount in bps
        fallback_min: Fallback minimum margin if no rule
        fallback_max: Fallback maximum margin if no rule

    Returns:
        Final margin in bps
    """
    if actions:
        # Use rule-based calculation
        result = apply_margin_rules(
            actions, base_margin, tier_adjustment,
            currency_factor, negotiated_discount
        )
        return result['total_margin_bps']
    else:
        # Fallback to default calculation
        total = base_margin + tier_adjustment + currency_factor - negotiated_discount

        if fallback_min is not None:
            total = max(total, fallback_min)

        if fallback_max is not None:
            total = min(total, fallback_max)

        return total
