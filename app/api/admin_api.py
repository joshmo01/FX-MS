"""
Admin API - CRUD endpoints for reference tables
"""
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from app.services.admin_service import admin_service, RESOURCE_CONFIG

router = APIRouter(prefix="/api/v1/fx/admin", tags=["admin"])


class AdminResponse(BaseModel):
    """Standard admin API response"""
    status: str
    data: Optional[Any] = None
    message: Optional[str] = None


class AdminItemRequest(BaseModel):
    """Generic item data for create/update"""
    class Config:
        extra = "allow"  # Allow additional fields


@router.get("/resources")
async def list_resources():
    """List all available resource types"""
    resources = []
    for resource_type, config in RESOURCE_CONFIG.items():
        resources.append({
            "type": resource_type,
            "id_field": config["id_field"],
            "file": config["file"]
        })

    return AdminResponse(
        status="success",
        data=resources,
        message=f"Found {len(resources)} resource types"
    )


@router.get("/{resource_type}")
async def get_all_items(resource_type: str):
    """Get all items in a resource table"""
    result = admin_service.get_resource(resource_type)

    return AdminResponse(
        status="success",
        data=result["items"],
        message=f"Retrieved {result['count']} items"
    )


@router.get("/{resource_type}/{item_id}")
async def get_item(resource_type: str, item_id: str):
    """Get a single item by ID"""
    item = admin_service.get_item(resource_type, item_id)

    return AdminResponse(
        status="success",
        data=item,
        message=f"Retrieved {item_id}"
    )


@router.post("/{resource_type}")
async def create_item(resource_type: str, item_data: Dict[str, Any] = Body(...)):
    """Create a new item"""
    created_item = admin_service.create_item(resource_type, item_data)

    # Reload engines after creation
    admin_service.reload_engines(resource_type)

    return AdminResponse(
        status="success",
        data=created_item,
        message=f"Successfully created {item_data.get(admin_service._get_id_field(resource_type))}"
    )


@router.put("/{resource_type}/{item_id}")
async def update_item(resource_type: str, item_id: str, item_data: Dict[str, Any] = Body(...)):
    """Update an existing item"""
    updated_item = admin_service.update_item(resource_type, item_id, item_data)

    # Reload engines after update
    admin_service.reload_engines(resource_type)

    return AdminResponse(
        status="success",
        data=updated_item,
        message=f"Successfully updated {item_id}"
    )


@router.delete("/{resource_type}/{item_id}")
async def delete_item(resource_type: str, item_id: str):
    """Delete an item"""
    success = admin_service.delete_item(resource_type, item_id)

    # Reload engines after deletion
    admin_service.reload_engines(resource_type)

    return AdminResponse(
        status="success",
        data={"deleted": success},
        message=f"Successfully deleted {item_id}"
    )


@router.post("/{resource_type}/reload")
async def reload_engines(resource_type: str):
    """Force reload of engines for a resource type"""
    success = admin_service.reload_engines(resource_type)

    return AdminResponse(
        status="success" if success else "warning",
        data={"reloaded": success},
        message="Engines reloaded" if success else "Reload completed with warnings"
    )


@router.get("/{resource_type}/validate/{item_id}")
async def validate_item(resource_type: str, item_id: str):
    """Validate an item without saving (for testing)"""
    item = admin_service.get_item(resource_type, item_id)

    try:
        admin_service._validate_item(resource_type, item, is_create=False)
        return AdminResponse(
            status="success",
            data={"valid": True},
            message="Item is valid"
        )
    except HTTPException as e:
        return AdminResponse(
            status="error",
            data={"valid": False, "errors": [e.detail]},
            message="Validation failed"
        )
