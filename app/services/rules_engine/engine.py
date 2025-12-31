"""
Rules Engine Core

Main orchestrator for rule evaluation with priority-based matching.
"""
import time
import logging
from typing import Optional, List
from datetime import datetime

from .models import (
    Rule, RuleType, TransactionContext, RuleEvaluationResult,
    RuleAuditLog
)
from .evaluator import RuleEvaluator
from .loader import get_loader, RuleLoader

logger = logging.getLogger(__name__)


class RulesEngine:
    """
    Core rules evaluation engine

    Singleton that orchestrates rule loading, evaluation, and matching
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.loader: RuleLoader = get_loader()
        self.evaluator = RuleEvaluator()
        self.audit_logs: List[RuleAuditLog] = []
        self._initialized = True
        logger.info("Rules Engine initialized")

    def evaluate(
        self,
        rule_type: str | RuleType,
        context: TransactionContext
    ) -> RuleEvaluationResult:
        """
        Evaluate rules against context and return highest priority match

        Args:
            rule_type: Type of rules to evaluate (PROVIDER_SELECTION or MARGIN_ADJUSTMENT)
            context: Transaction context with data

        Returns:
            RuleEvaluationResult with matched rule and actions, or use_default=True
        """
        start_time = time.time()

        # Convert string to enum if needed
        if isinstance(rule_type, str):
            rule_type = RuleType(rule_type)

        logger.debug(f"Evaluating {rule_type} rules")

        # Load applicable rules
        all_rules = self.loader.load_rules(rule_type)

        # Filter by validity and enabled status
        applicable_rules = self._filter_applicable_rules(all_rules, context.timestamp)

        logger.debug(f"Found {len(applicable_rules)} applicable {rule_type} rules")

        # Evaluate conditions
        matching_rules = []
        for rule in applicable_rules:
            try:
                if self.evaluator.evaluate_conditions(rule.conditions, context):
                    matching_rules.append(rule)
                    logger.debug(f"Rule {rule.rule_id} ({rule.rule_name}) matched")
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.rule_id}: {e}")
                continue

        # Sort by priority (highest first)
        matching_rules.sort(key=lambda r: r.priority, reverse=True)

        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000

        # Build result
        if matching_rules:
            winner = matching_rules[0]
            alternatives = matching_rules[1:3]  # Top 2 alternatives

            logger.info(
                f"Rule {winner.rule_id} ({winner.rule_name}) matched with priority {winner.priority}"
            )

            result = RuleEvaluationResult(
                matched=True,
                winning_rule=winner,
                actions=winner.actions,
                alternatives=alternatives,
                evaluation_time_ms=execution_time_ms,
                use_default=False
            )

            # Log audit trail
            self._log_audit(winner, context, True, execution_time_ms)

            return result

        else:
            logger.debug(f"No {rule_type} rules matched, using default behavior")

            result = RuleEvaluationResult(
                matched=False,
                winning_rule=None,
                actions=None,
                alternatives=[],
                evaluation_time_ms=execution_time_ms,
                use_default=True
            )

            # Log audit trail
            self._log_audit(None, context, False, execution_time_ms)

            return result

    def get_matching_rules(
        self,
        rule_type: str | RuleType,
        context: TransactionContext
    ) -> List[Rule]:
        """
        Get all matching rules for debugging/testing

        Args:
            rule_type: Type of rules to evaluate
            context: Transaction context

        Returns:
            List of all matching rules sorted by priority
        """
        if isinstance(rule_type, str):
            rule_type = RuleType(rule_type)

        all_rules = self.loader.load_rules(rule_type)
        applicable_rules = self._filter_applicable_rules(all_rules, context.timestamp)

        matching_rules = []
        for rule in applicable_rules:
            try:
                if self.evaluator.evaluate_conditions(rule.conditions, context):
                    matching_rules.append(rule)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.rule_id}: {e}")
                continue

        matching_rules.sort(key=lambda r: r.priority, reverse=True)
        return matching_rules

    def reload_rules(self) -> None:
        """Force reload of rules from configuration"""
        logger.info("Reloading rules")
        self.loader.reload_rules()

    def _filter_applicable_rules(self, rules: List[Rule], timestamp: datetime) -> List[Rule]:
        """
        Filter rules by enabled status and validity period

        Args:
            rules: All rules
            timestamp: Current timestamp

        Returns:
            List of applicable rules
        """
        applicable = []
        for rule in rules:
            # Must be enabled
            if not rule.enabled:
                continue

            # Must be within validity period
            if timestamp < rule.valid_from:
                continue

            if rule.valid_until and timestamp > rule.valid_until:
                continue

            applicable.append(rule)

        return applicable

    def _log_audit(
        self,
        rule: Optional[Rule],
        context: TransactionContext,
        matched: bool,
        execution_time_ms: float
    ) -> None:
        """Log rule evaluation to audit trail"""
        audit_entry = RuleAuditLog(
            rule_id=rule.rule_id if rule else None,
            rule_name=rule.rule_name if rule else None,
            context=context.model_dump(),
            matched=matched,
            executed_at=datetime.utcnow(),
            execution_time_ms=execution_time_ms,
            result={
                'matched': matched,
                'priority': rule.priority if rule else None
            }
        )

        self.audit_logs.append(audit_entry)

        # Keep only last 1000 entries to prevent memory issues
        if len(self.audit_logs) > 1000:
            self.audit_logs = self.audit_logs[-1000:]

    def get_audit_logs(self, limit: int = 100) -> List[RuleAuditLog]:
        """Get recent audit logs"""
        return self.audit_logs[-limit:]


# Convenience functions for easy import
_engine = None


def get_engine() -> RulesEngine:
    """Get singleton engine instance"""
    global _engine
    if _engine is None:
        _engine = RulesEngine()
    return _engine


def evaluate(rule_type: str | RuleType, context: TransactionContext) -> RuleEvaluationResult:
    """Convenience function for evaluating rules"""
    return get_engine().evaluate(rule_type, context)


def reload_rules() -> None:
    """Convenience function for reloading rules"""
    get_engine().reload_rules()
