"""
Admin Service - Business logic for Reference Tables CRUD operations
"""
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import HTTPException

# Resource configuration mapping
RESOURCE_CONFIG = {
    "customer-tiers": {
        "file": "config/customer_tiers.json",
        "id_field": "tier_id",
        "is_dict": True  # Data structure is a dict, not a list
    },
    "fx-providers": {
        "file": "config/fx_providers.json",
        "id_field": "provider_id",
        "is_dict": True
    },
    "treasury-rates": {
        "file": "config/treasury_rates.json",
        "id_field": "pair",
        "is_dict": True
    },
    "pricing-segments": {
        "file": "config/pricing_segments.json",
        "id_field": "segment_id",
        "is_dict": True
    },
    "pricing-tiers": {
        "file": "config/pricing_tiers.json",
        "id_field": "tier_id",
        "is_dict": True
    }
}


class AdminService:
    """Service for managing reference table CRUD operations"""

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.backup_dir = self.base_dir / "config" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.max_backups = 5

    def _get_file_path(self, resource_type: str) -> Path:
        """Get file path for a resource type"""
        if resource_type not in RESOURCE_CONFIG:
            raise HTTPException(status_code=400, detail=f"Unknown resource type: {resource_type}")

        file_path = self.base_dir / RESOURCE_CONFIG[resource_type]["file"]
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Config file not found: {file_path}")

        return file_path

    def _get_id_field(self, resource_type: str) -> str:
        """Get the ID field name for a resource type"""
        return RESOURCE_CONFIG[resource_type]["id_field"]

    def _is_dict_structure(self, resource_type: str) -> bool:
        """Check if resource uses dict structure (vs list)"""
        return RESOURCE_CONFIG[resource_type]["is_dict"]

    def _load_json(self, file_path: Path) -> Dict:
        """Load JSON file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Invalid JSON in config file: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error loading config: {str(e)}")

    def _save_json(self, file_path: Path, data: Dict):
        """Save JSON file with atomic write"""
        temp_file = file_path.with_suffix('.tmp')
        try:
            # Write to temp file
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            # Atomic replace
            temp_file.replace(file_path)
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise HTTPException(status_code=500, detail=f"Error saving config: {str(e)}")

    def _create_backup(self, resource_type: str, file_path: Path):
        """Create backup before modifying"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{resource_type}_backup_{timestamp}.json"
        backup_path = self.backup_dir / backup_name

        try:
            shutil.copy2(file_path, backup_path)
            self._cleanup_old_backups(resource_type)
        except Exception as e:
            print(f"Warning: Failed to create backup: {e}")

    def _cleanup_old_backups(self, resource_type: str):
        """Keep only the last N backups"""
        backups = sorted(
            self.backup_dir.glob(f"{resource_type}_backup_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        # Delete old backups
        for old_backup in backups[self.max_backups:]:
            try:
                old_backup.unlink()
            except Exception as e:
                print(f"Warning: Failed to delete old backup {old_backup}: {e}")

    def get_resource(self, resource_type: str) -> Dict:
        """Get all items in a resource"""
        file_path = self._get_file_path(resource_type)
        data = self._load_json(file_path)

        if self._is_dict_structure(resource_type):
            # Convert dict to list for API response
            return {"items": list(data.values()), "count": len(data)}
        else:
            return {"items": data, "count": len(data)}

    def get_item(self, resource_type: str, item_id: str) -> Dict:
        """Get a single item by ID"""
        file_path = self._get_file_path(resource_type)
        data = self._load_json(file_path)

        if self._is_dict_structure(resource_type):
            if item_id not in data:
                raise HTTPException(status_code=404, detail=f"Item not found: {item_id}")
            return data[item_id]
        else:
            # List structure - find by ID field
            id_field = self._get_id_field(resource_type)
            item = next((i for i in data if i.get(id_field) == item_id), None)
            if not item:
                raise HTTPException(status_code=404, detail=f"Item not found: {item_id}")
            return item

    def create_item(self, resource_type: str, item_data: Dict) -> Dict:
        """Create a new item"""
        file_path = self._get_file_path(resource_type)
        id_field = self._get_id_field(resource_type)

        # Validate item has ID field
        if id_field not in item_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {id_field}")

        item_id = item_data[id_field]

        # Validate item data
        self._validate_item(resource_type, item_data, is_create=True)

        # Create backup
        self._create_backup(resource_type, file_path)

        # Load current data
        data = self._load_json(file_path)

        # Check if item already exists
        if self._is_dict_structure(resource_type):
            if item_id in data:
                raise HTTPException(status_code=400, detail=f"Item already exists: {item_id}")
            data[item_id] = item_data
        else:
            if any(i.get(id_field) == item_id for i in data):
                raise HTTPException(status_code=400, detail=f"Item already exists: {item_id}")
            data.append(item_data)

        # Save updated data
        self._save_json(file_path, data)

        return item_data

    def update_item(self, resource_type: str, item_id: str, item_data: Dict) -> Dict:
        """Update an existing item"""
        file_path = self._get_file_path(resource_type)
        id_field = self._get_id_field(resource_type)

        # Ensure ID in data matches parameter
        if id_field in item_data and item_data[id_field] != item_id:
            raise HTTPException(status_code=400, detail=f"ID mismatch: {item_data[id_field]} != {item_id}")

        item_data[id_field] = item_id

        # Validate item data
        self._validate_item(resource_type, item_data, is_create=False)

        # Create backup
        self._create_backup(resource_type, file_path)

        # Load current data
        data = self._load_json(file_path)

        # Update item
        if self._is_dict_structure(resource_type):
            if item_id not in data:
                raise HTTPException(status_code=404, detail=f"Item not found: {item_id}")
            data[item_id] = item_data
        else:
            index = next((i for i, item in enumerate(data) if item.get(id_field) == item_id), None)
            if index is None:
                raise HTTPException(status_code=404, detail=f"Item not found: {item_id}")
            data[index] = item_data

        # Save updated data
        self._save_json(file_path, data)

        return item_data

    def delete_item(self, resource_type: str, item_id: str) -> bool:
        """Delete an item"""
        file_path = self._get_file_path(resource_type)
        id_field = self._get_id_field(resource_type)

        # Create backup
        self._create_backup(resource_type, file_path)

        # Load current data
        data = self._load_json(file_path)

        # Delete item
        if self._is_dict_structure(resource_type):
            if item_id not in data:
                raise HTTPException(status_code=404, detail=f"Item not found: {item_id}")
            del data[item_id]
        else:
            index = next((i for i, item in enumerate(data) if item.get(id_field) == item_id), None)
            if index is None:
                raise HTTPException(status_code=404, detail=f"Item not found: {item_id}")
            data.pop(index)

        # Save updated data
        self._save_json(file_path, data)

        return True

    def reload_engines(self, resource_type: str) -> bool:
        """Reload engines after config changes"""
        try:
            if resource_type in ["customer-tiers", "fx-providers", "treasury-rates"]:
                # Reload smart routing engine
                from app.services.smart_routing_engine import routing_engine
                if hasattr(routing_engine, 'reload_config'):
                    routing_engine.reload_config()

            if resource_type in ["pricing-segments", "pricing-tiers"]:
                # Reload pricing config
                from app.api import pricing
                if hasattr(pricing, 'reload_pricing_config'):
                    pricing.reload_pricing_config()

            return True
        except Exception as e:
            print(f"Warning: Failed to reload engines: {e}")
            return False

    def _validate_item(self, resource_type: str, item_data: Dict, is_create: bool = True):
        """Validate item data based on resource type"""

        if resource_type == "customer-tiers":
            self._validate_customer_tier(item_data)
        elif resource_type == "fx-providers":
            self._validate_fx_provider(item_data)
        elif resource_type == "treasury-rates":
            self._validate_treasury_rate(item_data)
        elif resource_type == "pricing-segments":
            self._validate_pricing_segment(item_data)
        elif resource_type == "pricing-tiers":
            self._validate_pricing_tier(item_data)

    def _validate_customer_tier(self, data: Dict):
        """Validate customer tier data"""
        required_fields = ["tier_id", "name", "min_annual_volume_usd", "markup_discount_pct",
                          "spread_reduction_bps", "priority_routing", "dedicated_treasury",
                          "max_transaction_usd", "stp_threshold_usd"]

        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        # Validate numeric ranges
        if data["min_annual_volume_usd"] < 0:
            raise HTTPException(status_code=400, detail="min_annual_volume_usd must be >= 0")

        if not 0 <= data["markup_discount_pct"] <= 100:
            raise HTTPException(status_code=400, detail="markup_discount_pct must be 0-100")

        if data["spread_reduction_bps"] < 0:
            raise HTTPException(status_code=400, detail="spread_reduction_bps must be >= 0")

        if data["max_transaction_usd"] <= 0:
            raise HTTPException(status_code=400, detail="max_transaction_usd must be > 0")

    def _validate_fx_provider(self, data: Dict):
        """Validate FX provider data"""
        required_fields = ["provider_id", "name", "type", "reliability_score",
                          "avg_latency_ms", "markup_bps", "supported_pairs", "operating_hours"]

        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        # Validate type
        valid_types = ["MARKET_DATA", "INTERNAL", "CORRESPONDENT", "DOMESTIC", "FINTECH"]
        if data["type"] not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid type. Must be one of: {valid_types}")

        # Validate numeric ranges
        if not 0 <= data["reliability_score"] <= 1:
            raise HTTPException(status_code=400, detail="reliability_score must be 0-1")

        if data["avg_latency_ms"] <= 0:
            raise HTTPException(status_code=400, detail="avg_latency_ms must be > 0")

        if data["markup_bps"] < 0:
            raise HTTPException(status_code=400, detail="markup_bps must be >= 0")

        # Validate supported_pairs is a list
        if not isinstance(data["supported_pairs"], list):
            raise HTTPException(status_code=400, detail="supported_pairs must be an array")

    def _validate_treasury_rate(self, data: Dict):
        """Validate treasury rate data"""
        required_fields = ["pair", "bid", "ask", "mid", "min_margin_bps", "position"]

        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        # Validate currency pair format (6 letters)
        if not data["pair"].isalpha() or len(data["pair"]) != 6:
            raise HTTPException(status_code=400, detail="pair must be 6-letter currency code (e.g., USDINR)")

        # Validate bid < ask
        if data["bid"] >= data["ask"]:
            raise HTTPException(status_code=400, detail="bid must be less than ask")

        # Validate mid is between bid and ask
        expected_mid = (data["bid"] + data["ask"]) / 2
        if abs(data["mid"] - expected_mid) > 0.01:
            raise HTTPException(status_code=400, detail=f"mid should be {expected_mid:.4f} (average of bid and ask)")

        if data["min_margin_bps"] < 0:
            raise HTTPException(status_code=400, detail="min_margin_bps must be >= 0")

        # Validate position
        valid_positions = ["LONG", "SHORT", "NEUTRAL"]
        if data["position"] not in valid_positions:
            raise HTTPException(status_code=400, detail=f"Invalid position. Must be one of: {valid_positions}")

    def _validate_pricing_segment(self, data: Dict):
        """Validate pricing segment data"""
        required_fields = ["segment_id", "base_margin_bps", "min_margin_bps", "max_margin_bps",
                          "volume_discount_eligible", "negotiated_rates_allowed"]

        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        # Validate margin relationships
        if not (data["min_margin_bps"] <= data["base_margin_bps"] <= data["max_margin_bps"]):
            raise HTTPException(
                status_code=400,
                detail="Margin must satisfy: min_margin_bps <= base_margin_bps <= max_margin_bps"
            )

    def _validate_pricing_tier(self, data: Dict):
        """Validate pricing tier data"""
        required_fields = ["tier_id", "min_amount", "adjustment_bps", "description"]

        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

        # Validate amount range
        if data["min_amount"] < 0:
            raise HTTPException(status_code=400, detail="min_amount must be >= 0")

        if data.get("max_amount") is not None and data["max_amount"] <= data["min_amount"]:
            raise HTTPException(status_code=400, detail="max_amount must be > min_amount (or null for highest tier)")

        # Validate TIER_1 starts at 0
        if data["tier_id"] == "TIER_1" and data["min_amount"] != 0:
            raise HTTPException(status_code=400, detail="TIER_1 must start at min_amount = 0")


# Global service instance
admin_service = AdminService()
