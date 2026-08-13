import unittest

from tools.autopilot.error_handling import make_event, user_message


class ErrorHandlingTests(unittest.TestCase):
    def test_event_contains_stable_code_and_trace(self):
        event = make_event("VAL-INVENTORY-001")
        self.assertEqual(event.code, "VAL-INVENTORY-001")
        self.assertTrue(event.trace_id.startswith("TRC-"))

    def test_user_message_is_clear(self):
        message = user_message(make_event("VAL-INVENTORY-001"))
        self.assertIn("Auswirkung:", message)
        self.assertIn("Was ist zu tun:", message)
        self.assertIn("Fehler-ID:", message)


if __name__ == "__main__":
    unittest.main()
