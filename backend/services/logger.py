"""Structured JSON Logger — Security & API monitoring.

Logs auth events, rate limits, API errors, and session activity
as JSON lines for Render log aggregation and monitoring.

All logs go to stdout (Render captures stdout automatically).
"""

import json
import time
import sys
from datetime import datetime, timezone


class SecurityLogger:
    """Structured security event logger."""

    def _emit(self, event_type: str, **kwargs) -> None:
        """Write a JSON log line to stdout."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            **kwargs,
        }
        # JSON line to stdout (Render captures this)
        print(json.dumps(entry, default=str), file=sys.stdout, flush=True)

    # ── Auth Events ──

    def auth_success(self, user_id: str, ip: str, endpoint: str) -> None:
        self._emit(
            "auth.success",
            user_id=user_id,
            ip=ip,
            endpoint=endpoint,
        )

    def auth_failure(self, ip: str, reason: str, endpoint: str) -> None:
        self._emit(
            "auth.failure",
            ip=ip,
            reason=reason,
            endpoint=endpoint,
            severity="WARNING",
        )

    # ── Rate Limit Events ──

    def rate_limit_hit(self, category: str, identifier: str, limit: int, window: int) -> None:
        self._emit(
            "rate_limit.hit",
            category=category,
            identifier=identifier,
            limit=limit,
            window_seconds=window,
            severity="WARNING",
        )

    # ── API Events ──

    def api_error(self, endpoint: str, error: str, status_code: int, ip: str = "", user_id: str = "") -> None:
        self._emit(
            "api.error",
            endpoint=endpoint,
            error=error,
            status_code=status_code,
            ip=ip,
            user_id=user_id,
            severity="ERROR",
        )

    def api_request(self, method: str, endpoint: str, status_code: int, duration_ms: float, ip: str = "", user_id: str = "") -> None:
        self._emit(
            "api.request",
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            duration_ms=round(duration_ms, 2),
            ip=ip,
            user_id=user_id,
        )

    # ── Session Events ──

    def session_created(self, session_id: str, user_id: str, business_type: str) -> None:
        self._emit(
            "session.created",
            session_id=session_id,
            user_id=user_id,
            business_type=business_type,
        )

    def session_access_denied(self, session_id: str, user_id: str, ip: str) -> None:
        self._emit(
            "session.access_denied",
            session_id=session_id,
            user_id=user_id,
            ip=ip,
            severity="WARNING",
        )

    # ── Agent Events ──

    def agent_completed(self, session_id: str, agent_name: str, duration_seconds: float) -> None:
        self._emit(
            "agent.completed",
            session_id=session_id,
            agent_name=agent_name,
            duration_seconds=round(duration_seconds, 1),
        )

    def agent_error(self, session_id: str, agent_name: str, error: str) -> None:
        self._emit(
            "agent.error",
            session_id=session_id,
            agent_name=agent_name,
            error=error,
            severity="ERROR",
        )


# Global logger instance
security_logger = SecurityLogger()
