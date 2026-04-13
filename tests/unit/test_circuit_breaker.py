"""Unit tests for lambda_tools.shared.circuit_breaker."""

import time
from unittest.mock import patch

from lambda_tools.shared.circuit_breaker import (
    CircuitBreaker,
    CircuitOpenError,
    CircuitState,
)


class TestCircuitBreakerClosed:
    """Tests for CLOSED state behavior."""

    def test_initial_state_is_closed(self):
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED

    def test_successful_call_returns_result(self):
        cb = CircuitBreaker()
        result = cb.call(lambda x: x * 2, 5)
        assert result == 10

    def test_single_failure_stays_closed(self):
        cb = CircuitBreaker(failure_threshold=5)
        try:
            cb.call(_fail)
        except RuntimeError:
            pass
        assert cb.state == CircuitState.CLOSED

    def test_failures_below_threshold_stay_closed(self):
        cb = CircuitBreaker(failure_threshold=5)
        for _ in range(4):
            try:
                cb.call(_fail)
            except RuntimeError:
                pass
        assert cb.state == CircuitState.CLOSED


class TestCircuitBreakerOpen:
    """Tests for OPEN state behavior."""

    def test_opens_after_threshold_failures(self):
        cb = CircuitBreaker(failure_threshold=5, failure_window=60)
        for _ in range(5):
            try:
                cb.call(_fail)
            except RuntimeError:
                pass
        assert cb.state == CircuitState.OPEN

    def test_open_raises_circuit_open_error(self):
        cb = _make_open_breaker()
        try:
            cb.call(lambda: "should not run")
            assert False, "Expected CircuitOpenError"
        except CircuitOpenError:
            pass

    def test_open_does_not_call_fn(self):
        cb = _make_open_breaker()
        called = []
        try:
            cb.call(lambda: called.append(True))
        except CircuitOpenError:
            pass
        assert called == []


class TestCircuitBreakerHalfOpen:
    """Tests for HALF_OPEN state behavior."""

    def test_transitions_to_half_open_after_cooldown(self):
        cb = CircuitBreaker(failure_threshold=2, cooldown=0.1)
        for _ in range(2):
            try:
                cb.call(_fail)
            except RuntimeError:
                pass
        assert cb.state == CircuitState.OPEN
        time.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN

    def test_half_open_success_closes_circuit(self):
        cb = CircuitBreaker(failure_threshold=2, cooldown=0.1)
        for _ in range(2):
            try:
                cb.call(_fail)
            except RuntimeError:
                pass
        time.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN
        result = cb.call(lambda: "ok")
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    def test_half_open_failure_reopens_circuit(self):
        cb = CircuitBreaker(failure_threshold=2, cooldown=0.1)
        for _ in range(2):
            try:
                cb.call(_fail)
            except RuntimeError:
                pass
        time.sleep(0.15)
        assert cb.state == CircuitState.HALF_OPEN
        try:
            cb.call(_fail)
        except RuntimeError:
            pass
        assert cb.state == CircuitState.OPEN


class TestCircuitBreakerWindow:
    """Tests for failure window expiry."""

    def test_old_failures_outside_window_are_ignored(self):
        cb = CircuitBreaker(failure_threshold=3, failure_window=0.1)
        for _ in range(2):
            try:
                cb.call(_fail)
            except RuntimeError:
                pass
        time.sleep(0.15)  # let failures expire
        try:
            cb.call(_fail)
        except RuntimeError:
            pass
        # Only 1 failure in window now, should stay closed
        assert cb.state == CircuitState.CLOSED


# -- helpers --

def _fail():
    raise RuntimeError("boom")


def _make_open_breaker() -> CircuitBreaker:
    cb = CircuitBreaker(failure_threshold=2, cooldown=30)
    for _ in range(2):
        try:
            cb.call(_fail)
        except RuntimeError:
            pass
    return cb
