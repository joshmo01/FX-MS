"""
Deals API - REST endpoints for FX Treasury Deals
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from app.models.deal import (
    Deal, DealStatus, DealListResponse, Utilization, AuditLogEntry, BestRateResponse,
    CreateDealRequest, UpdateDealRequest, SubmitDealRequest,
    ApproveDealRequest, RejectDealRequest, UtilizeDealRequest, CancelDealRequest
)
from app.services.deals_service import deals_service

router = APIRouter(prefix="/api/v1/fx/deals", tags=["Deals"])


# CRUD Endpoints

@router.post("", response_model=Deal)
async def create_deal(request: CreateDealRequest):
    """Create a new deal in DRAFT status"""
    deal, error = deals_service.create_deal(request)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return deal


@router.get("", response_model=DealListResponse)
async def list_deals(
    status: Optional[str] = Query(None, description="Filter by status"),
    currency_pair: Optional[str] = Query(None, description="Filter by currency pair"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """List deals with optional filters"""
    deals, total = deals_service.list_deals(status, currency_pair, page, page_size)
    return DealListResponse(deals=deals, total=total, page=page, page_size=page_size)


@router.get("/active")
async def get_active_deals(
    currency_pair: str = Query(..., description="Currency pair"),
    customer_tier: Optional[str] = Query(None, description="Customer tier")
):
    """Get active deals for a currency pair"""
    deals = deals_service.get_active_deals(currency_pair, customer_tier)
    return {"deals": deals, "count": len(deals)}


@router.get("/best-rate", response_model=BestRateResponse)
async def get_best_rate(
    currency_pair: str = Query(..., description="Currency pair"),
    side: str = Query(..., description="BUY or SELL"),
    amount: float = Query(..., gt=0, description="Transaction amount"),
    customer_tier: str = Query(..., description="Customer tier"),
    treasury_rate: float = Query(..., gt=0, description="Current treasury rate")
):
    """Get best available rate (deal or treasury)"""
    return deals_service.get_best_rate(currency_pair, side, amount, customer_tier, treasury_rate)


@router.get("/{deal_id}", response_model=Deal)
async def get_deal(deal_id: str):
    """Get deal by ID"""
    deal = deals_service.get_deal(deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal


@router.put("/{deal_id}", response_model=Deal)
async def update_deal(deal_id: str, request: UpdateDealRequest, updated_by: str = Query(...)):
    """Update deal (only DRAFT status)"""
    deal, error = deals_service.update_deal(deal_id, request, updated_by)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return deal


@router.delete("/{deal_id}", response_model=Deal)
async def cancel_deal(deal_id: str, request: CancelDealRequest):
    """Cancel a deal"""
    deal, error = deals_service.cancel_deal(deal_id, request.cancelled_by, request.cancellation_reason)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return deal


# Workflow Endpoints

@router.post("/{deal_id}/submit", response_model=Deal)
async def submit_deal(deal_id: str, request: SubmitDealRequest):
    """Submit deal for approval (DRAFT -> PENDING_APPROVAL)"""
    deal, error = deals_service.submit_deal(deal_id, request.submitted_by)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return deal


@router.post("/{deal_id}/approve", response_model=Deal)
async def approve_deal(deal_id: str, request: ApproveDealRequest):
    """Approve deal (PENDING_APPROVAL -> ACTIVE)"""
    deal, error = deals_service.approve_deal(deal_id, request.approved_by, request.comments)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return deal


@router.post("/{deal_id}/reject", response_model=Deal)
async def reject_deal(deal_id: str, request: RejectDealRequest):
    """Reject deal with reason"""
    deal, error = deals_service.reject_deal(deal_id, request.rejected_by, request.rejection_reason)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return deal


# Utilization Endpoints

@router.post("/{deal_id}/utilize", response_model=Utilization)
async def utilize_deal(deal_id: str, request: UtilizeDealRequest):
    """Utilize part of a deal"""
    utilization, error = deals_service.utilize_deal(deal_id, request)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return utilization


@router.get("/{deal_id}/utilizations")
async def get_utilizations(deal_id: str):
    """Get utilization history for a deal"""
    utilizations = deals_service.get_utilizations(deal_id)
    return {"utilizations": utilizations, "count": len(utilizations)}


@router.get("/{deal_id}/audit-log")
async def get_audit_log(deal_id: str):
    """Get audit log for a deal"""
    logs = deals_service.get_audit_log(deal_id)
    return {"audit_log": logs, "count": len(logs)}
