"""Tests for Step 12.6 request lifecycle state."""

import unittest

from legacy_gateway.gateway.requests import (
    InvalidRequestTransition,
    RequestLifecycle,
    RequestTracker,
)
from legacy_gateway.protocol.messages import RequestMessage


def make_request(request_id: str = "R-12-6") -> RequestMessage:
    return RequestMessage(
        request_id=request_id,
        session_id="S-1",
        device_id="D-1",
        operation="chat",
        model="mock-model",
    )


class RequestStateTests(unittest.TestCase):
    def test_new_record_starts_at_new(self) -> None:
        tracker = RequestTracker()
        record = tracker.create(make_request())
        self.assertEqual(record.state, RequestLifecycle.NEW)
        self.assertEqual(record.history, [RequestLifecycle.NEW])
        self.assertFalse(record.terminal)

    def test_happy_path_reaches_success(self) -> None:
        tracker = RequestTracker()
        tracker.create(make_request())
        for state in (
            RequestLifecycle.RECEIVED,
            RequestLifecycle.AUTHORIZED,
            RequestLifecycle.COST_CHECKED,
            RequestLifecycle.RUNNING,
            RequestLifecycle.SUCCESS,
        ):
            tracker.transition("R-12-6", state)
        record = tracker.require("R-12-6")
        self.assertEqual(record.state, RequestLifecycle.SUCCESS)
        self.assertTrue(record.terminal)

    def test_running_can_end_in_failure(self) -> None:
        tracker = RequestTracker()
        tracker.create(make_request())
        for state in (
            RequestLifecycle.RECEIVED,
            RequestLifecycle.AUTHORIZED,
            RequestLifecycle.COST_CHECKED,
            RequestLifecycle.RUNNING,
            RequestLifecycle.FAILURE,
        ):
            tracker.transition("R-12-6", state)
        self.assertEqual(tracker.require("R-12-6").state, RequestLifecycle.FAILURE)

    def test_running_can_end_in_uncertain(self) -> None:
        tracker = RequestTracker()
        tracker.create(make_request())
        for state in (
            RequestLifecycle.RECEIVED,
            RequestLifecycle.AUTHORIZED,
            RequestLifecycle.COST_CHECKED,
            RequestLifecycle.RUNNING,
            RequestLifecycle.UNCERTAIN,
        ):
            tracker.transition("R-12-6", state)
        self.assertEqual(tracker.require("R-12-6").state, RequestLifecycle.UNCERTAIN)

    def test_invalid_transition_is_rejected(self) -> None:
        tracker = RequestTracker()
        tracker.create(make_request())
        with self.assertRaises(InvalidRequestTransition):
            tracker.transition("R-12-6", RequestLifecycle.RUNNING)

    def test_terminal_state_cannot_transition(self) -> None:
        tracker = RequestTracker()
        tracker.create(make_request())
        for state in (
            RequestLifecycle.RECEIVED,
            RequestLifecycle.AUTHORIZED,
            RequestLifecycle.COST_CHECKED,
            RequestLifecycle.RUNNING,
            RequestLifecycle.SUCCESS,
        ):
            tracker.transition("R-12-6", state)
        with self.assertRaises(InvalidRequestTransition):
            tracker.transition("R-12-6", RequestLifecycle.RUNNING)

    def test_duplicate_request_id_is_rejected(self) -> None:
        tracker = RequestTracker()
        tracker.create(make_request())
        with self.assertRaises(ValueError):
            tracker.create(make_request())

    def test_unknown_request_is_rejected(self) -> None:
        tracker = RequestTracker()
        with self.assertRaises(KeyError):
            tracker.require("missing")

    def test_can_transition_to_is_non_mutating(self) -> None:
        tracker = RequestTracker()
        record = tracker.create(make_request())
        self.assertTrue(record.can_transition_to(RequestLifecycle.RECEIVED))
        self.assertFalse(record.can_transition_to(RequestLifecycle.RUNNING))
        self.assertEqual(record.state, RequestLifecycle.NEW)

    def test_tracker_is_separate_for_each_logical_request(self) -> None:
        tracker = RequestTracker()
        tracker.create(make_request("R-1"))
        tracker.create(make_request("R-2"))
        tracker.transition("R-1", RequestLifecycle.RECEIVED)
        self.assertEqual(tracker.require("R-1").state, RequestLifecycle.RECEIVED)
        self.assertEqual(tracker.require("R-2").state, RequestLifecycle.NEW)
        self.assertEqual(len(tracker), 2)


if __name__ == "__main__":
    unittest.main()
