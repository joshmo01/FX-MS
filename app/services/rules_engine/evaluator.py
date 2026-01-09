"""
Rules Engine Condition Evaluator

Evaluates rule conditions against transaction contexts with support for
nested AND/OR/NOT logic and extensible custom attributes.
"""
from typing import Any, Optional
from datetime import datetime, time
import re
from .models import (
    RuleConditions, Criterion, CriterionOperator, ConditionOperator,
    TransactionContext
)


class RuleEvaluator:
    """Evaluates rule conditions against transaction contexts"""

    def evaluate_conditions(self, conditions: RuleConditions, context: TransactionContext) -> bool:
        """
        Recursively evaluate nested conditions with AND/OR/NOT logic

        Args:
            conditions: Rule conditions to evaluate
            context: Transaction context with data

        Returns:
            bool: True if conditions match, False otherwise
        """
        operator = conditions.operator

        if operator == ConditionOperator.AND:
            return all(self._evaluate_single(criterion, context) for criterion in conditions.criteria)

        elif operator == ConditionOperator.OR:
            return any(self._evaluate_single(criterion, context) for criterion in conditions.criteria)

        elif operator == ConditionOperator.NOT:
            if len(conditions.criteria) != 1:
                raise ValueError("NOT operator requires exactly one criterion")
            return not self._evaluate_single(conditions.criteria[0], context)

        return False

    def _evaluate_single(self, item: Any, context: TransactionContext) -> bool:
        """Evaluate a single item (criterion or nested conditions)"""
        if isinstance(item, RuleConditions):
            return self.evaluate_conditions(item, context)
        elif isinstance(item, Criterion):
            return self.evaluate_criterion(item, context)
        else:
            raise ValueError(f"Invalid criterion type: {type(item)}")

    def evaluate_criterion(self, criterion: Criterion, context: TransactionContext) -> bool:
        """
        Evaluate individual criterion against context

        Args:
            criterion: Single criterion to evaluate
            context: Transaction context

        Returns:
            bool: True if criterion matches
        """
        field_value = self.get_field_value(context, criterion.field)

        # If field doesn't exist or is None, only EQUALS None can match
        if field_value is None:
            return criterion.operator == CriterionOperator.EQUALS and criterion.value is None

        operator = criterion.operator

        # Comparison operators
        if operator == CriterionOperator.EQUALS:
            return field_value == criterion.value

        elif operator == CriterionOperator.NOT_EQUALS:
            return field_value != criterion.value

        elif operator == CriterionOperator.GREATER_THAN:
            return self._safe_compare(field_value, criterion.value, lambda a, b: a > b)

        elif operator == CriterionOperator.GREATER_THAN_OR_EQUAL:
            return self._safe_compare(field_value, criterion.value, lambda a, b: a >= b)

        elif operator == CriterionOperator.LESS_THAN:
            return self._safe_compare(field_value, criterion.value, lambda a, b: a < b)

        elif operator == CriterionOperator.LESS_THAN_OR_EQUAL:
            return self._safe_compare(field_value, criterion.value, lambda a, b: a <= b)

        # Set operators
        elif operator == CriterionOperator.IN:
            if not criterion.values:
                return False
            return field_value in criterion.values

        elif operator == CriterionOperator.NOT_IN:
            if not criterion.values:
                return True
            return field_value not in criterion.values

        elif operator == CriterionOperator.CONTAINS:
            return self._contains(field_value, criterion.value)

        elif operator == CriterionOperator.NOT_CONTAINS:
            return not self._contains(field_value, criterion.value)

        # Range operators
        elif operator == CriterionOperator.BETWEEN:
            if not criterion.values or len(criterion.values) != 2:
                return False
            return criterion.values[0] <= field_value <= criterion.values[1]

        elif operator == CriterionOperator.NOT_BETWEEN:
            if not criterion.values or len(criterion.values) != 2:
                return True
            return not (criterion.values[0] <= field_value <= criterion.values[1])

        # Temporal operators
        elif operator == CriterionOperator.WITHIN_HOURS:
            return self._check_time_range(field_value, criterion.value, within=True)

        elif operator == CriterionOperator.OUTSIDE_HOURS:
            return self._check_time_range(field_value, criterion.value, within=False)

        # String pattern operators
        elif operator == CriterionOperator.MATCHES_REGEX:
            return self._matches_regex(field_value, criterion.value)

        elif operator == CriterionOperator.STARTS_WITH:
            return str(field_value).startswith(str(criterion.value))

        elif operator == CriterionOperator.ENDS_WITH:
            return str(field_value).endswith(str(criterion.value))

        return False

    def get_field_value(self, context: TransactionContext, field: str) -> Any:
        """
        Extract field value from context

        Checks predefined fields first, then custom_attributes

        Args:
            context: Transaction context
            field: Field name

        Returns:
            Field value or None if not found
        """
        # Try predefined fields first
        if hasattr(context, field):
            return getattr(context, field)

        # Try custom attributes
        if context.custom_attributes and field in context.custom_attributes:
            return context.custom_attributes[field]

        return None

    def _safe_compare(self, a: Any, b: Any, comparator) -> bool:
        """Safely compare values, handling type mismatches"""
        try:
            return comparator(a, b)
        except (TypeError, ValueError):
            return False

    def _contains(self, container: Any, item: Any) -> bool:
        """Check if container contains item"""
        try:
            if isinstance(container, str):
                return str(item) in container
            elif isinstance(container, (list, tuple, set)):
                return item in container
            elif isinstance(container, dict):
                return item in container.keys()
            return False
        except (TypeError, AttributeError):
            return False

    def _check_time_range(self, field_value: Any, range_spec: dict, within: bool) -> bool:
        """
        Check if time is within or outside specified hours

        Args:
            field_value: Time value (datetime, time, or HH:MM string)
            range_spec: Dict with 'start', 'end', optional 'timezone'
            within: True to check within range, False for outside

        Returns:
            bool: Match result
        """
        if not range_spec or 'start' not in range_spec or 'end' not in range_spec:
            return False

        try:
            # Parse time from field_value
            if isinstance(field_value, datetime):
                current_time = field_value.time()
            elif isinstance(field_value, time):
                current_time = field_value
            elif isinstance(field_value, str):
                # Assume HH:MM format
                hour, minute = map(int, field_value.split(':'))
                current_time = time(hour, minute)
            else:
                # If no time provided, use context timestamp
                return False

            # Parse range
            start_hour, start_minute = map(int, range_spec['start'].split(':'))
            end_hour, end_minute = map(int, range_spec['end'].split(':'))
            start_time = time(start_hour, start_minute)
            end_time = time(end_hour, end_minute)

            # Check if within range
            is_within = start_time <= current_time <= end_time

            return is_within if within else not is_within

        except (ValueError, AttributeError, KeyError):
            return False

    def _matches_regex(self, field_value: Any, pattern: str) -> bool:
        """Check if field value matches regex pattern"""
        try:
            return bool(re.match(pattern, str(field_value)))
        except (TypeError, re.error):
            return False


# Singleton instance
_evaluator = RuleEvaluator()


def evaluate_conditions(conditions: RuleConditions, context: TransactionContext) -> bool:
    """Convenience function for evaluating conditions"""
    return _evaluator.evaluate_conditions(conditions, context)


def evaluate_criterion(criterion: Criterion, context: TransactionContext) -> bool:
    """Convenience function for evaluating a single criterion"""
    return _evaluator.evaluate_criterion(criterion, context)
