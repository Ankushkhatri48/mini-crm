from datetime import datetime
from database.db import get_session
from database.models import AuditLog
import streamlit as st


def log_action(action: str, detail: str = ""):
    """Write an audit log entry for the current user."""
    try:
        username = st.session_state.get("username", "unknown")
        db = get_session()
        entry = AuditLog(
            username=username,
            action=action,
            detail=detail[:500],  # cap detail length
            timestamp=datetime.utcnow(),
        )
        db.add(entry)
        db.commit()
        db.close()
    except Exception:
        pass  # audit logging must never crash the app


def get_recent_logs(limit: int = 50) -> list:
    db = get_session()
    try:
        return (
            db.query(AuditLog)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
            .all()
        )
    finally:
        db.close()
