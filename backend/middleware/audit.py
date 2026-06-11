"""
Audit logging helper
Log wie wat wanneer deed — AVG compliant
"""

from fastapi import Request
from datetime import datetime, timezone
from typing import Optional
import logging

logger = logging.getLogger("audit")


async def log_action(
    request: Request,
    action: str,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    metadata: Optional[dict] = None,
):
    """
    Log een actie naar de audit log.
    In productie: schrijf naar database audit_log tabel.
    Nu: log naar stdout (Railway pikt dit op).
    """
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "user_id": user_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "ip_address": ip,
        "user_agent": user_agent[:200] if user_agent else None,  # truncate — geen persoonsgegeven logging
        "metadata": metadata or {},
    }

    logger.info("[AUDIT] %s", entry)
