# Add this helper function at the top of the DealsService class

def _parse_datetime(self, dt_string):
    """Parse datetime string and return naive UTC datetime"""
    if dt_string is None:
        return None
    dt_str = dt_string.replace("Z", "+00:00")
    try:
        from datetime import timezone
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo is not None:
            # Convert to UTC and make naive
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except:
        return datetime.fromisoformat(dt_string.replace("Z", ""))

def _check_expiry(self):
    """Check and update expired deals"""
    now = datetime.utcnow()
    for deal in self.deals:
        if deal["status"] == DealStatus.ACTIVE.value:
            valid_until = self._parse_datetime(deal["valid_until"])
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
