"""
FX Rules Engine

Priority-based rules engine for FX provider selection and margin adjustments.
Supports extensible custom parameters from API JSON payloads.
"""
from .engine import RulesEngine, get_engine, evaluate, reload_rules
from .models import (
    Rule, RuleType, TransactionContext, PricingContext, ProviderContext,
    RuleEvaluationResult, ProviderSelectionAction, MarginAdjustmentAction
)
from .evaluator import RuleEvaluator, evaluate_conditions, evaluate_criterion
from .loader import get_loader, RuleLoader
from .providers import apply_provider_rules, filter_providers_by_rules
from .pricing import apply_margin_rules, calculate_margin_with_rules

__all__ = [
    # Engine
    'RulesEngine',
    'get_engine',
    'evaluate',
    'reload_rules',

    # Models
    'Rule',
    'RuleType',
    'TransactionContext',
    'PricingContext',
    'ProviderContext',
    'RuleEvaluationResult',
    'ProviderSelectionAction',
    'MarginAdjustmentAction',

    # Evaluator
    'RuleEvaluator',
    'evaluate_conditions',
    'evaluate_criterion',

    # Loader
    'get_loader',
    'RuleLoader',

    # Actions
    'apply_provider_rules',
    'filter_providers_by_rules',
    'apply_margin_rules',
    'calculate_margin_with_rules',
]
