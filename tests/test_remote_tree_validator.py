import unittest

from tools.autopilot.remote_tree_validator import parse_tree


class RemoteTreeValidatorTests(unittest.TestCase):
    def test_empty_input_is_empty_tree(self):
        self.assertEqual(parse_tree([]), {})


if __name__ == "__main__":
    unittest.main()
