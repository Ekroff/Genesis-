"""Rate Limiter — In-memory sliding window rate limiting.

No Redis required. Uses a dictionary of request timestamps per key.
Automatically cleans up expired entries.

Usage:
    limiter = RateLimiter()

    @app.post("/api/launch")
    async def launch(request: Request, user_id: str = Depends(get_current_user)):
        limiter.check("launch", user_id, max_requests=5, window_seconds=3600)
        ...
"""

import time
from collections import defaultdict
from threading import Lock
from fastapi import HTTPException, Request


class RateLimiter:
    """Thread-safe sliding window rate limiter."""

    def __init__(self):
        # key -> list of timestamps
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # Clean up every 5 minutes

    def check(
        self,
        category: str,
        identifier: str,
        max_requests: int,
        window_seconds: int,
    ) -> None:
        """Check rate limit. Raises 429 if exceeded.

        Args:
            category: e.g., "launch", "generate-names", "invoice"
            identifier: user_id, IP, or session_id
            max_requests: max allowed requests in the window
            window_seconds: sliding window size in seconds
        """
        key = f"{category}:{identifier}"
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            # Remove expired timestamps
            self._requests[key] = [
                ts for ts in self._requests[key] if ts > cutoff
            ]

            if len(self._requests[key]) >= max_requests:
                # Calculate retry-after
                oldest = self._requests[key][0] if self._requests[key] else now
                retry_after = int(oldest + window_seconds - now) + 1

                from services.logger import security_logger
                security_logger.rate_limit_hit(
                    category=category,
                    identifier=identifier,
                    limit=max_requests,
                    window=window_seconds,
                )

                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    headers={"Retry-After": str(retry_after)},
                )

            # Record this request
            self._requests[key].append(now)

            # Periodic cleanup of stale keys
            if now - self._last_cleanup > self._cleanup_interval:
                self._cleanup(now)

    def _cleanup(self, now: float) -> None:
        """Remove keys with no recent requests."""
        stale_keys = [
            key for key, timestamps in self._requests.items()
            if not timestamps or timestamps[-1] < now - 7200  # 2 hours stale
        ]
        for key in stale_keys:
            del self._requests[key]
        self._last_cleanup = now

    def get_usage(self, category: str, identifier: str, window_seconds: int) -> int:
        """Get current request count for a key (for monitoring)."""
        key = f"{category}:{identifier}"
        cutoff = time.time() - window_seconds
        with self._lock:
            return len([ts for ts in self._requests.get(key, []) if ts > cutoff])


# ═══════ Global limiter instance ═══════

rate_limiter = RateLimiter()


# ═══════ Preset limit checkers ═══════

def limit_launch(user_id: str) -> None:
    """5 launches per hour per user."""
    rate_limiter.check("launch", user_id, max_requests=5, window_seconds=3600)


def limit_name_gen(request: Request) -> None:
    """10 name generations per hour per IP."""
    ip = request.client.host if request.client else "unknown"
    rate_limiter.check("generate-names", ip, max_requests=10, window_seconds=3600)


def limit_retry(user_id: str) -> None:
    """10 retries per hour per user."""
    rate_limiter.check("retry", user_id, max_requests=10, window_seconds=3600)


def limit_invoice(session_id: str) -> None:
    """30 invoices per hour per session."""
    rate_limiter.check("invoice", session_id, max_requests=30, window_seconds=3600)


def limit_email(session_id: str) -> None:
    """3 summary emails per hour per session."""
    rate_limiter.check("email", session_id, max_requests=3, window_seconds=3600)


def limit_general(request: Request) -> None:
    """60 requests per minute per IP (general fallback)."""
    ip = request.client.host if request.client else "unknown"
    rate_limiter.check("general", ip, max_requests=60, window_seconds=60)
