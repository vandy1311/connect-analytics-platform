"""In-memory circuit breaker for protecting downstream calls."""

import time
from enum import Enum


class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitOpenError(Exception):
    """Raised when a call is attempted while the circuit is OPEN."""

    def __init__(self, retry_after: float = 0.0):
        self.retry_after = retry_after
        super().__init__(
            f"Circuit breaker is OPEN. Retry after {retry_after:.1f}s."
        )


class CircuitBreaker:
    """In-memory circuit breaker.

    States:
        CLOSED  — normal operation; calls pass through.
        OPEN    — after ``failure_threshold`` consecutive failures within
                  ``failure_window`` seconds, all calls are rejected immediately.
        HALF_OPEN — after ``cooldown`` seconds in OPEN state, one probe call
                    is allowed. Success → CLOSED, failure → OPEN.

    Args:
        failure_threshold: Consecutive failures before opening. Default 5.
        failure_window: Window in seconds for counting failures. Default 60.
        cooldown: Seconds to wait in OPEN before transitioning to HALF_OPEN. Default 30.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        failure_window: float = 60.0,
        cooldown: float = 30.0,
    ):
        self.failure_threshold = failure_threshold
        self.failure_window = failure_window
        self.cooldown = cooldown

        self._state = CircuitState.CLOSED
        self._failure_timestamps: list[float] = []
        self._opened_at: float = 0.0

    @property
    def state(self) -> CircuitState:
        """Current circuit state, accounting for cooldown transitions."""
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._opened_at >= self.cooldown:
                self._state = CircuitState.HALF_OPEN
        return self._state

    def call(self, fn, *args, **kwargs):
        """Execute *fn* through the circuit breaker.

        Args:
            fn: Callable to invoke.
            *args: Positional arguments forwarded to *fn*.
            **kwargs: Keyword arguments forwarded to *fn*.

        Returns:
            The return value of *fn*.

        Raises:
            CircuitOpenError: If the circuit is OPEN.
        """
        current = self.state

        if current == CircuitState.OPEN:
            retry_after = self.cooldown - (time.monotonic() - self._opened_at)
            raise CircuitOpenError(retry_after=max(retry_after, 0.0))

        try:
            result = fn(*args, **kwargs)
        except Exception:
            self._record_failure()
            raise

        # Success path
        if current == CircuitState.HALF_OPEN:
            self._reset()
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _record_failure(self) -> None:
        """Record a failure and potentially open the circuit."""
        now = time.monotonic()
        self._failure_timestamps.append(now)

        # Prune failures outside the window
        cutoff = now - self.failure_window
        self._failure_timestamps = [
            t for t in self._failure_timestamps if t >= cutoff
        ]

        if self._state == CircuitState.HALF_OPEN:
            # Probe call failed — go back to OPEN
            self._open(now)
        elif len(self._failure_timestamps) >= self.failure_threshold:
            self._open(now)

    def _open(self, now: float) -> None:
        self._state = CircuitState.OPEN
        self._opened_at = now

    def _reset(self) -> None:
        """Reset to CLOSED state and clear failure history."""
        self._state = CircuitState.CLOSED
        self._failure_timestamps.clear()
        self._opened_at = 0.0
