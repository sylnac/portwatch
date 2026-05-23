"""Tests for portwatch.scheduler."""

import time
import threading
import pytest

from portwatch.scheduler import Scheduler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _counting_callback(counter: list) -> None:
    """Append a timestamp each time it is called."""
    counter.append(time.monotonic())


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestScheduler:
    def test_raises_on_non_positive_interval(self):
        with pytest.raises(ValueError, match="interval must be positive"):
            Scheduler(interval=0, callback=lambda: None)

        with pytest.raises(ValueError, match="interval must be positive"):
            Scheduler(interval=-1.0, callback=lambda: None)

    def test_not_running_before_start(self):
        s = Scheduler(interval=1.0, callback=lambda: None)
        assert not s.running

    def test_running_after_start(self):
        s = Scheduler(interval=10.0, callback=lambda: None)
        s.start()
        try:
            assert s.running
        finally:
            s.stop()

    def test_not_running_after_stop(self):
        s = Scheduler(interval=10.0, callback=lambda: None)
        s.start()
        s.stop()
        assert not s.running

    def test_callback_is_invoked(self):
        calls: list = []
        s = Scheduler(interval=0.05, callback=lambda: calls.append(1))
        s.start()
        time.sleep(0.18)  # allow ~3 ticks
        s.stop()
        assert len(calls) >= 2

    def test_stop_interrupts_sleep(self):
        """stop() should return well before the long interval expires."""
        s = Scheduler(interval=60.0, callback=lambda: None)
        s.start()
        # First callback fires immediately; then it would sleep 60 s.
        time.sleep(0.05)
        t0 = time.monotonic()
        s.stop(timeout=2.0)
        elapsed = time.monotonic() - t0
        assert elapsed < 2.0, f"stop() took too long: {elapsed:.2f}s"

    def test_double_start_is_safe(self):
        s = Scheduler(interval=10.0, callback=lambda: None)
        s.start()
        s.start()  # should log a warning, not raise
        assert s.running
        s.stop()

    def test_callback_exception_does_not_kill_scheduler(self):
        """An exception in the callback must not terminate the thread."""
        calls: list = []

        def bad_callback():
            calls.append(1)
            raise RuntimeError("boom")

        s = Scheduler(interval=0.05, callback=bad_callback)
        s.start()
        time.sleep(0.18)
        s.stop()
        assert len(calls) >= 2, "scheduler should keep running after callback error"
