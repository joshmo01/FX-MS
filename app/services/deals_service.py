"""
Deals Service - Business logic for FX Treasury Deals
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from app.models.deal import (
    Deal, DealStatus, DealSide, CustomerTier, AuditAction,
    CreateDealRequest, UpdateDealRequest, UtilizeDealRequest,
    Utilization, AuditLogEntry, BestRateResponse
)


class DealsService:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.deals_file = self.data_dir / "deals.json"
        self.utilizations_file = self.data_dir / "utilizations.json"
        self.audit_file = self.data_dir / "deal_audit_log.json"
        
        for file in [self.deals_file, self.utilizations_file, self.audit_file]:
            if not file.exists():
                file.write_text("[]")
        
        self.deals: List[dict] = self._load_json(self.deals_file)
        self.utilizations: List[dict] = self._load_json(self.utilizations_file)
        self.audit_log: List[dict] = self._load_json(self.audit_file)
    
    def _load_json(self, file: Path) -> list:
        try:
            return json.loads(file.read_text())
        except:
            return []
    
    def _save_deals(self):
        self.deals_file.write_text(json.dumps(self.deals, indent=2, default=str))
    
    def _save_utilizations(self):
        self.utilizations_file.write_text(json.dumps(self.utilizations, indent=2, default=str))
    
    def _save_audit_log(self):
        self.audit_file.write_text(json.dumps(self.audit_log, indent=2, default=str))
    
    def _generate_deal_id(self) -> str:
        date_str = datetime.utcnow().strftime("%Y%m%d")
        count = len([d for d in self.deals if d["deal_id"].startswith(f"DEAL-{date_str}")]) + 1
        return f"DEAL-{date_str}-{count:04d}"
    
    def _add_audit_log(self, deal_id: str, action: AuditAction, actor: str, 
                       old_values: dict = None, new_values: dict = None, details: str = None):
        entry = {
            "log_id": f"LOG-{uuid.uuid4().hex[:8].upper()}",
            "deal_id": deal_id,
            "action": action.value,
            "actor": actor,
            "timestamp": datetime.utcnow().isoformat(),
            "old_values": old_values,
            "new_values": new_values,
            "details": details
        }
        self.audit_log.append(entry)
        self._save_audit_log()
    
    def _calculate_spread_bps(self, buy_rate: float, sell_rate: float) -> float:
        mid_rate = (buy_rate + sell_rate) / 2
        spread = sell_rate - buy_rate
        return round((spread / mid_rate) * 10000, 2)
    
    def _parse_datetime(self, dt_string):
        """Parse datetime string and return naive UTC datetime"""
        if dt_string is None:
            return None
        try:
            dt_str = str(dt_string).replace("Z", "+00:00")
            dt = datetime.fromisoformat(dt_str)
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            return dt
        except:
            try:
                return datetime.fromisoformat(str(dt_string).replace("Z", ""))
            except:
                return None
    
    def _check_expiry(self):
        now = datetime.utcnow()
        for deal in self.deals:
            if deal["status"] == DealStatus.ACTIVE.value:
                valid_until = self._parse_datetime(deal.get("valid_until"))
                if valid_until and now > valid_until:
                    old_status = deal["status"]
                    deal["status"] = DealStatus.EXPIRED.value
                    deal["updated_at"] = now.isoformat()
                    self._add_audit_log(
                        deal["deal_id"], AuditAction.EXPIRED, "SYSTEM",
                        old_values={"status": old_status},
                        new_values={"status": DealStatus.EXPIRED.value},
                        details="Deal expired automatically"
                    )
        self._save_deals()
    
    def create_deal(self, request: CreateDealRequest) -> Tuple[Deal, str]:
        if request.buy_rate >= request.sell_rate:
            return None, "Buy rate must be less than sell rate"
        
        if request.valid_from >= request.valid_until:
            return None, "valid_from must be before valid_until"
        
        validity_days = (request.valid_until - request.valid_from).days
        if validity_days > 7:
            return None, "Maximum validity period is 7 days"
        
        now = datetime.utcnow()
        deal_id = self._generate_deal_id()
        
        deal = {
            "deal_id": deal_id,
            "currency_pair": request.currency_pair.upper(),
            "side": request.side.value,
            "buy_rate": request.buy_rate,
            "sell_rate": request.sell_rate,
            "spread_bps": self._calculate_spread_bps(request.buy_rate, request.sell_rate),
            "amount": request.amount,
            "available_amount": request.amount,
            "utilized_amount": 0,
            "valid_from": request.valid_from.isoformat(),
            "valid_until": request.valid_until.isoformat(),
            "status": DealStatus.DRAFT.value,
            "customer_tier": request.customer_tier.value if request.customer_tier else None,
            "min_amount": request.min_amount,
            "max_amount_per_txn": request.max_amount_per_txn,
            "created_by": request.created_by,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "submitted_by": None,
            "submitted_at": None,
            "approved_by": None,
            "approved_at": None,
            "rejected_by": None,
            "rejected_at": None,
            "rejection_reason": None,
            "cancelled_by": None,
            "cancelled_at": None,
            "cancellation_reason": None,
            "notes": request.notes
        }
        
        self.deals.append(deal)
        self._save_deals()
        
        self._add_audit_log(
            deal_id, AuditAction.CREATED, request.created_by,
            new_values=deal,
            details=f"Deal created for {request.currency_pair}"
        )
        
        return Deal(**deal), None
    
    def get_deal(self, deal_id: str) -> Optional[Deal]:
        self._check_expiry()
        for deal in self.deals:
            if deal["deal_id"] == deal_id:
                return Deal(**deal)
        return None
    
    def list_deals(self, status: str = None, currency_pair: str = None, 
                   page: int = 1, page_size: int = 20) -> Tuple[List[Deal], int]:
        self._check_expiry()
        
        filtered = self.deals.copy()
        
        if status:
            filtered = [d for d in filtered if d["status"] == status]
        
        if currency_pair:
            filtered = [d for d in filtered if d["currency_pair"] == currency_pair.upper()]
        
        # Sort by created_at descending (newest first) before pagination
        filtered.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        
        return [Deal(**d) for d in filtered[start:end]], total
    
    def update_deal(self, deal_id: str, request: UpdateDealRequest, updated_by: str) -> Tuple[Deal, str]:
        deal = None
        deal_idx = None
        for idx, d in enumerate(self.deals):
            if d["deal_id"] == deal_id:
                deal = d
                deal_idx = idx
                break
        
        if not deal:
            return None, "Deal not found"
        
        if deal["status"] != DealStatus.DRAFT.value:
            return None, "Only DRAFT deals can be modified"
        
        old_values = deal.copy()
        
        if request.buy_rate is not None:
            deal["buy_rate"] = request.buy_rate
        if request.sell_rate is not None:
            deal["sell_rate"] = request.sell_rate
        
        if deal["buy_rate"] >= deal["sell_rate"]:
            return None, "Buy rate must be less than sell rate"
        
        deal["spread_bps"] = self._calculate_spread_bps(deal["buy_rate"], deal["sell_rate"])
        
        if request.amount is not None:
            deal["amount"] = request.amount
            deal["available_amount"] = request.amount
        if request.valid_from is not None:
            deal["valid_from"] = request.valid_from.isoformat()
        if request.valid_until is not None:
            deal["valid_until"] = request.valid_until.isoformat()
        if request.customer_tier is not None:
            deal["customer_tier"] = request.customer_tier.value
        if request.min_amount is not None:
            deal["min_amount"] = request.min_amount
        if request.max_amount_per_txn is not None:
            deal["max_amount_per_txn"] = request.max_amount_per_txn
        if request.notes is not None:
            deal["notes"] = request.notes
        
        deal["updated_at"] = datetime.utcnow().isoformat()
        
        self.deals[deal_idx] = deal
        self._save_deals()
        
        self._add_audit_log(
            deal_id, AuditAction.MODIFIED, updated_by,
            old_values=old_values,
            new_values=deal,
            details="Deal modified"
        )
        
        return Deal(**deal), None
    
    def submit_deal(self, deal_id: str, submitted_by: str) -> Tuple[Deal, str]:
        deal = None
        deal_idx = None
        for idx, d in enumerate(self.deals):
            if d["deal_id"] == deal_id:
                deal = d
                deal_idx = idx
                break
        
        if not deal:
            return None, "Deal not found"
        
        if deal["status"] != DealStatus.DRAFT.value:
            return None, f"Cannot submit deal with status {deal['status']}"
        
        old_status = deal["status"]
        deal["status"] = DealStatus.PENDING_APPROVAL.value
        deal["submitted_by"] = submitted_by
        deal["submitted_at"] = datetime.utcnow().isoformat()
        deal["updated_at"] = datetime.utcnow().isoformat()
        
        self.deals[deal_idx] = deal
        self._save_deals()
        
        self._add_audit_log(
            deal_id, AuditAction.SUBMITTED, submitted_by,
            old_values={"status": old_status},
            new_values={"status": deal["status"]},
            details="Deal submitted for approval"
        )
        
        return Deal(**deal), None
    
    def approve_deal(self, deal_id: str, approved_by: str, comments: str = None) -> Tuple[Deal, str]:
        deal = None
        deal_idx = None
        for idx, d in enumerate(self.deals):
            if d["deal_id"] == deal_id:
                deal = d
                deal_idx = idx
                break
        
        if not deal:
            return None, "Deal not found"
        
        if deal["status"] != DealStatus.PENDING_APPROVAL.value:
            return None, f"Cannot approve deal with status {deal['status']}"
        
        if deal["created_by"] == approved_by:
            return None, "Self-approval is not allowed"
        
        old_status = deal["status"]
        deal["status"] = DealStatus.ACTIVE.value
        deal["approved_by"] = approved_by
        deal["approved_at"] = datetime.utcnow().isoformat()
        deal["updated_at"] = datetime.utcnow().isoformat()
        
        self.deals[deal_idx] = deal
        self._save_deals()
        
        self._add_audit_log(
            deal_id, AuditAction.APPROVED, approved_by,
            old_values={"status": old_status},
            new_values={"status": deal["status"], "approved_by": approved_by},
            details=comments or "Deal approved"
        )
        
        return Deal(**deal), None
    
    def reject_deal(self, deal_id: str, rejected_by: str, rejection_reason: str) -> Tuple[Deal, str]:
        deal = None
        deal_idx = None
        for idx, d in enumerate(self.deals):
            if d["deal_id"] == deal_id:
                deal = d
                deal_idx = idx
                break
        
        if not deal:
            return None, "Deal not found"
        
        if deal["status"] != DealStatus.PENDING_APPROVAL.value:
            return None, f"Cannot reject deal with status {deal['status']}"
        
        old_status = deal["status"]
        deal["status"] = DealStatus.REJECTED.value
        deal["rejected_by"] = rejected_by
        deal["rejected_at"] = datetime.utcnow().isoformat()
        deal["rejection_reason"] = rejection_reason
        deal["updated_at"] = datetime.utcnow().isoformat()
        
        self.deals[deal_idx] = deal
        self._save_deals()
        
        self._add_audit_log(
            deal_id, AuditAction.REJECTED, rejected_by,
            old_values={"status": old_status},
            new_values={"status": deal["status"], "rejection_reason": rejection_reason},
            details=rejection_reason
        )
        
        return Deal(**deal), None
    
    def cancel_deal(self, deal_id: str, cancelled_by: str, cancellation_reason: str) -> Tuple[Deal, str]:
        deal = None
        deal_idx = None
        for idx, d in enumerate(self.deals):
            if d["deal_id"] == deal_id:
                deal = d
                deal_idx = idx
                break
        
        if not deal:
            return None, "Deal not found"
        
        if deal["status"] in [DealStatus.FULLY_UTILIZED.value, DealStatus.CANCELLED.value]:
            return None, f"Cannot cancel deal with status {deal['status']}"
        
        old_status = deal["status"]
        deal["status"] = DealStatus.CANCELLED.value
        deal["cancelled_by"] = cancelled_by
        deal["cancelled_at"] = datetime.utcnow().isoformat()
        deal["cancellation_reason"] = cancellation_reason
        deal["updated_at"] = datetime.utcnow().isoformat()
        
        self.deals[deal_idx] = deal
        self._save_deals()
        
        self._add_audit_log(
            deal_id, AuditAction.CANCELLED, cancelled_by,
            old_values={"status": old_status},
            new_values={"status": deal["status"], "cancellation_reason": cancellation_reason},
            details=cancellation_reason
        )
        
        return Deal(**deal), None
    
    def utilize_deal(self, deal_id: str, request: UtilizeDealRequest) -> Tuple[Utilization, str]:
        self._check_expiry()
        
        deal = None
        deal_idx = None
        for idx, d in enumerate(self.deals):
            if d["deal_id"] == deal_id:
                deal = d
                deal_idx = idx
                break
        
        if not deal:
            return None, "Deal not found"
        
        if deal["status"] != DealStatus.ACTIVE.value:
            return None, f"Cannot utilize deal with status {deal['status']}"
        
        now = datetime.utcnow()
        valid_from = self._parse_datetime(deal["valid_from"])
        valid_until = self._parse_datetime(deal["valid_until"])
        
        if valid_from and now < valid_from:
            return None, "Deal is not yet valid"
        
        if valid_until and now > valid_until:
            return None, "Deal has expired"
        
        if deal["customer_tier"] and deal["customer_tier"] != request.customer_tier.value:
            return None, f"Deal is restricted to {deal['customer_tier']} tier"
        
        if request.amount < deal["min_amount"]:
            return None, f"Minimum transaction amount is {deal['min_amount']}"
        
        if deal["max_amount_per_txn"] and request.amount > deal["max_amount_per_txn"]:
            return None, f"Maximum transaction amount is {deal['max_amount_per_txn']}"
        
        if request.amount > deal["available_amount"]:
            return None, f"Requested amount exceeds available amount ({deal['available_amount']})"
        
        rate_applied = deal["sell_rate"] if deal["side"] == DealSide.SELL.value else deal["buy_rate"]
        
        deal["available_amount"] -= request.amount
        deal["utilized_amount"] += request.amount
        deal["updated_at"] = now.isoformat()
        
        if deal["available_amount"] == 0:
            deal["status"] = DealStatus.FULLY_UTILIZED.value
        
        self.deals[deal_idx] = deal
        self._save_deals()
        
        utilization = {
            "utilization_id": f"UTL-{uuid.uuid4().hex[:8].upper()}",
            "deal_id": deal_id,
            "amount": request.amount,
            "rate_applied": rate_applied,
            "customer_id": request.customer_id,
            "customer_tier": request.customer_tier.value,
            "transaction_ref": request.transaction_ref,
            "utilized_at": now.isoformat()
        }
        
        self.utilizations.append(utilization)
        self._save_utilizations()
        
        self._add_audit_log(
            deal_id, AuditAction.UTILIZED, request.customer_id,
            new_values={
                "amount": request.amount,
                "rate_applied": rate_applied,
                "available_amount": deal["available_amount"],
                "utilized_amount": deal["utilized_amount"]
            },
            details=f"Utilized {request.amount} at rate {rate_applied}"
        )
        
        return Utilization(**utilization), None
    
    def get_utilizations(self, deal_id: str) -> List[Utilization]:
        return [Utilization(**u) for u in self.utilizations if u["deal_id"] == deal_id]
    
    def get_audit_log(self, deal_id: str) -> List[AuditLogEntry]:
        return [AuditLogEntry(**log) for log in self.audit_log if log["deal_id"] == deal_id]
    
    def get_active_deals(self, currency_pair: str, customer_tier: str = None) -> List[Deal]:
        self._check_expiry()
        
        now = datetime.utcnow()
        active = []
        
        for deal in self.deals:
            if deal["status"] != DealStatus.ACTIVE.value:
                continue
            
            if deal["currency_pair"] != currency_pair.upper():
                continue
            
            if deal["customer_tier"] and customer_tier:
                if deal["customer_tier"] != customer_tier:
                    continue
            
            valid_from = self._parse_datetime(deal["valid_from"])
            valid_until = self._parse_datetime(deal["valid_until"])
            
            if valid_from and valid_until and valid_from <= now <= valid_until:
                active.append(Deal(**deal))
        
        return active
    
    def get_best_rate(self, currency_pair: str, side: str, amount: float, 
                      customer_tier: str, treasury_rate: float) -> BestRateResponse:
        active_deals = self.get_active_deals(currency_pair, customer_tier)
        eligible_deals = [d for d in active_deals if d.available_amount >= amount]
        
        best_deal = None
        best_deal_rate = None
        
        for deal in eligible_deals:
            deal_rate = deal.sell_rate if side == "SELL" else deal.buy_rate
            
            if best_deal_rate is None:
                best_deal = deal
                best_deal_rate = deal_rate
            elif side == "BUY" and deal_rate < best_deal_rate:
                best_deal = deal
                best_deal_rate = deal_rate
            elif side == "SELL" and deal_rate > best_deal_rate:
                best_deal = deal
                best_deal_rate = deal_rate
        
        if best_deal:
            if side == "BUY":
                savings_bps = (treasury_rate - best_deal_rate) / treasury_rate * 10000
            else:
                savings_bps = (best_deal_rate - treasury_rate) / treasury_rate * 10000
            
            return BestRateResponse(
                currency_pair=currency_pair,
                side=side,
                rate=best_deal_rate,
                source="DEAL",
                deal_id=best_deal.deal_id,
                available_amount=best_deal.available_amount,
                valid_until=best_deal.valid_until,
                treasury_rate=treasury_rate,
                savings_bps=round(savings_bps, 2)
            )
        
        return BestRateResponse(
            currency_pair=currency_pair,
            side=side,
            rate=treasury_rate,
            source="TREASURY",
            deal_id=None,
            available_amount=None,
            valid_until=None,
            treasury_rate=treasury_rate,
            savings_bps=0
        )


deals_service = DealsService()
