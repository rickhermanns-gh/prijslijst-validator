"""
Audit logging helper
Log wie wat wanneer deed — AVG compliant
Schrijft naar audit_log tabel én stdout (Railway pikt beide op).
"""

from fastapi import Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional
import logging
import uuid

logger = logging.getLogger("audit")


async def log_action(
    request: Request,
    action: str,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    metadata: Optional[dict] = None,
    db: Optional[Session] = None,
):
    """
    Log een actie naar stdout én de audit_log DB tabel.
    db is optioneel — als het ontbreekt, wordt alleen naar stdout gelogd.
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
        "metadata": metadata or {},
    }

    logger.info("[AUDIT] %s", entry)

    # Schrijf naar DB als sessie beschikbaar is
    if db is not None:
        try:
            from models import AuditLog

            # Probeer session_id te extraheren uit resource_id als resource_type = upload_session
            session_uuid = None
            if resource_type == "upload_session" and resource_id:
                try:
                    session_uuid = uuid.UUID(resource_id)
                except ValueError:
                    pass

            user_uuid = None
            if user_id:
                try:
                    user_uuid = uuid.UUID(user_id)
                except ValueError:
                    pass

            log_entry = AuditLog(
                user_id=user_uuid,
                action=action,
                session_id=session_uuid,
                resource_type=resource_type,
                resource_id=resource_id,
                metadata_=metadata or {},
                ip_address=ip[:45] if ip else None,
                user_agent=user_agent[:200] if user_agent else None,
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            # Audit logging mag de request nooit blokkeren
            logger.warning("[AUDIT] DB write mislukt: %s", e)
