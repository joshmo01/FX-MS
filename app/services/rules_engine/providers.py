"""
Provider Selection Rule Actions

Handles application of provider selection rules to filter and override providers.
"""
from typing import List, Optional, Dict
import logging

from .models import ProviderSelectionAction

logger = logging.getLogger(__name__)


def apply_provider_rules(
    actions: ProviderSelectionAction,
    available_providers: List[str]
) -> Dict[str, any]:
    """
    Apply provider selection rule actions

    Args:
        actions: Provider selection actions from matching rule
        available_providers: List of all available provider IDs

    Returns:
        Dict with filtered providers and routing objective
    """
    result = {
        'eligible_providers': available_providers.copy(),
        'routing_objective_override': None,
        'force_provider': False
    }

    # Handle preferred providers
    if actions.preferred_providers:
        # Filter to only preferred providers that are available
        preferred_available = [
            p for p in actions.preferred_providers
            if p in available_providers
        ]

        if preferred_available:
            result['eligible_providers'] = preferred_available
            logger.debug(f"Filtered to preferred providers: {preferred_available}")
        else:
            logger.warning(
                f"None of the preferred providers {actions.preferred_providers} "
                f"are available in {available_providers}"
            )

    # Handle excluded providers
    if actions.excluded_providers:
        result['eligible_providers'] = [
            p for p in result['eligible_providers']
            if p not in actions.excluded_providers
        ]
        logger.debug(f"Excluded providers: {actions.excluded_providers}")

    # Handle routing objective override
    if actions.routing_objective_override:
        result['routing_objective_override'] = actions.routing_objective_override
        logger.debug(f"Routing objective overridden to: {actions.routing_objective_override}")

    # Handle force provider
    if actions.force_provider and result['eligible_providers']:
        # If force_provider is True, take only the first eligible provider
        result['force_provider'] = True
        result['eligible_providers'] = [result['eligible_providers'][0]]
        logger.debug(f"Force provider mode: using {result['eligible_providers'][0]}")

    return result


def filter_providers_by_rules(
    preferred: Optional[List[str]],
    excluded: Optional[List[str]],
    available: List[str]
) -> List[str]:
    """
    Simple filtering of providers by preferred and excluded lists

    Args:
        preferred: Optional list of preferred provider IDs
        excluded: Optional list of excluded provider IDs
        available: List of all available provider IDs

    Returns:
        Filtered list of provider IDs
    """
    result = available.copy()

    # Apply preferred filter
    if preferred:
        preferred_available = [p for p in preferred if p in result]
        if preferred_available:
            result = preferred_available

    # Apply exclusions
    if excluded:
        result = [p for p in result if p not in excluded]

    return result
