"""
Rules Engine Configuration Loader

Loads rules from JSON files with in-memory caching.
Designed for future database migration with abstract interface.
"""
import json
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import logging

from .models import Rule, RuleType

logger = logging.getLogger(__name__)


class RuleLoader(ABC):
    """Abstract interface for loading rules"""

    @abstractmethod
    def load_rules(self, rule_type: Optional[RuleType] = None) -> List[Rule]:
        """Load rules, optionally filtered by type"""
        pass

    @abstractmethod
    def reload_rules(self) -> None:
        """Force reload of rules (clear cache)"""
        pass

    @abstractmethod
    def save_rule(self, rule: Rule) -> bool:
        """Save a single rule"""
        pass

    @abstractmethod
    def delete_rule(self, rule_id: str) -> bool:
        """Delete a rule by ID"""
        pass


class JsonRuleLoader(RuleLoader):
    """
    JSON-based rule loader with in-memory caching

    Loads rules from /config/rules/*.json files with 5-minute TTL cache
    """

    def __init__(self, config_dir: str = "config/rules"):
        self.config_dir = Path(config_dir)
        self._cache: Dict[RuleType, List[Rule]] = {}
        self._cache_timestamp: Dict[RuleType, datetime] = {}
        self._cache_ttl = timedelta(minutes=5)

        # File mapping for rule types
        self._file_mapping = {
            RuleType.PROVIDER_SELECTION: "provider_rules.json",
            RuleType.MARGIN_ADJUSTMENT: "pricing_rules.json"
        }

    def load_rules(self, rule_type: Optional[RuleType] = None) -> List[Rule]:
        """
        Load rules from JSON files with caching

        Args:
            rule_type: Optional filter by rule type

        Returns:
            List of rules
        """
        if rule_type:
            return self._load_rules_by_type(rule_type)
        else:
            # Load all rule types
            all_rules = []
            for rt in RuleType:
                all_rules.extend(self._load_rules_by_type(rt))
            return all_rules

    def _load_rules_by_type(self, rule_type: RuleType) -> List[Rule]:
        """Load rules for a specific type with caching"""
        # Check cache
        if self._is_cache_valid(rule_type):
            logger.debug(f"Loading {rule_type} rules from cache")
            return self._cache[rule_type]

        # Load from file
        logger.info(f"Loading {rule_type} rules from JSON file")
        rules = self._load_from_file(rule_type)

        # Update cache
        self._cache[rule_type] = rules
        self._cache_timestamp[rule_type] = datetime.utcnow()

        return rules

    def _is_cache_valid(self, rule_type: RuleType) -> bool:
        """Check if cached rules are still valid"""
        if rule_type not in self._cache or rule_type not in self._cache_timestamp:
            return False

        age = datetime.utcnow() - self._cache_timestamp[rule_type]
        return age < self._cache_ttl

    def _load_from_file(self, rule_type: RuleType) -> List[Rule]:
        """Load rules from JSON file"""
        filename = self._file_mapping.get(rule_type)
        if not filename:
            logger.warning(f"No file mapping for rule type: {rule_type}")
            return []

        file_path = self.config_dir / filename

        if not file_path.exists():
            logger.warning(f"Rules file not found: {file_path}")
            return []

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            rules = []
            for rule_data in data.get('rules', []):
                try:
                    # Parse datetime fields (remove timezone to avoid comparison issues)
                    if 'valid_from' in rule_data:
                        dt = datetime.fromisoformat(
                            rule_data['valid_from'].replace('Z', '+00:00')
                        )
                        rule_data['valid_from'] = dt.replace(tzinfo=None)
                    if 'valid_until' in rule_data and rule_data['valid_until']:
                        dt = datetime.fromisoformat(
                            rule_data['valid_until'].replace('Z', '+00:00')
                        )
                        rule_data['valid_until'] = dt.replace(tzinfo=None)

                    # Parse metadata datetime fields
                    if 'metadata' in rule_data:
                        if 'created_at' in rule_data['metadata']:
                            dt = datetime.fromisoformat(
                                rule_data['metadata']['created_at'].replace('Z', '+00:00')
                            )
                            rule_data['metadata']['created_at'] = dt.replace(tzinfo=None)
                        if 'updated_at' in rule_data['metadata'] and rule_data['metadata']['updated_at']:
                            dt = datetime.fromisoformat(
                                rule_data['metadata']['updated_at'].replace('Z', '+00:00')
                            )
                            rule_data['metadata']['updated_at'] = dt.replace(tzinfo=None)

                    rule = Rule(**rule_data)
                    rules.append(rule)
                except Exception as e:
                    logger.error(f"Error parsing rule {rule_data.get('rule_id', 'unknown')}: {e}")
                    continue

            logger.info(f"Loaded {len(rules)} {rule_type} rules from {filename}")
            return rules

        except Exception as e:
            logger.error(f"Error loading rules from {file_path}: {e}")
            return []

    def reload_rules(self) -> None:
        """Force cache reload"""
        logger.info("Forcing rules cache reload")
        self._cache.clear()
        self._cache_timestamp.clear()

    def save_rule(self, rule: Rule) -> bool:
        """
        Save a rule to JSON file

        Args:
            rule: Rule to save

        Returns:
            bool: Success status
        """
        filename = self._file_mapping.get(rule.rule_type)
        if not filename:
            logger.error(f"No file mapping for rule type: {rule.rule_type}")
            return False

        file_path = self.config_dir / filename

        try:
            # Load existing rules
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data = json.load(f)
            else:
                data = {'version': '1.0.0', 'last_updated': datetime.utcnow().isoformat() + 'Z', 'rules': []}

            # Find and update or append
            rules = data.get('rules', [])
            rule_dict = json.loads(rule.model_dump_json())

            # Convert datetime objects back to ISO strings
            if 'valid_from' in rule_dict:
                rule_dict['valid_from'] = rule.valid_from.isoformat() + 'Z'
            if 'valid_until' in rule_dict and rule.valid_until:
                rule_dict['valid_until'] = rule.valid_until.isoformat() + 'Z'
            if 'metadata' in rule_dict:
                rule_dict['metadata']['created_at'] = rule.metadata.created_at.isoformat() + 'Z'
                if rule.metadata.updated_at:
                    rule_dict['metadata']['updated_at'] = rule.metadata.updated_at.isoformat() + 'Z'

            # Update or append
            found = False
            for i, existing_rule in enumerate(rules):
                if existing_rule.get('rule_id') == rule.rule_id:
                    rules[i] = rule_dict
                    found = True
                    break

            if not found:
                rules.append(rule_dict)

            data['rules'] = rules
            data['last_updated'] = datetime.utcnow().isoformat() + 'Z'

            # Write back
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)

            # Clear cache to force reload
            self.reload_rules()

            logger.info(f"Saved rule {rule.rule_id} to {filename}")
            return True

        except Exception as e:
            logger.error(f"Error saving rule {rule.rule_id}: {e}")
            return False

    def delete_rule(self, rule_id: str) -> bool:
        """
        Delete a rule from JSON file

        Args:
            rule_id: ID of rule to delete

        Returns:
            bool: Success status
        """
        # Search across all rule types
        for rule_type, filename in self._file_mapping.items():
            file_path = self.config_dir / filename

            if not file_path.exists():
                continue

            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                rules = data.get('rules', [])
                original_count = len(rules)

                # Filter out the rule to delete
                rules = [r for r in rules if r.get('rule_id') != rule_id]

                if len(rules) < original_count:
                    # Rule was found and removed
                    data['rules'] = rules
                    data['last_updated'] = datetime.utcnow().isoformat() + 'Z'

                    with open(file_path, 'w') as f:
                        json.dump(data, f, indent=2)

                    # Clear cache
                    self.reload_rules()

                    logger.info(f"Deleted rule {rule_id} from {filename}")
                    return True

            except Exception as e:
                logger.error(f"Error deleting rule {rule_id} from {filename}: {e}")
                continue

        logger.warning(f"Rule {rule_id} not found")
        return False


# Singleton instance
_loader = None


def get_loader() -> RuleLoader:
    """Get singleton loader instance"""
    global _loader
    if _loader is None:
        _loader = JsonRuleLoader()
    return _loader
