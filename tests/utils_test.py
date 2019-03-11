from os import path
from pathlib import Path
import unittest

from utils import get_hole_dicts, get_hole_value_assignments


class GetHoleValueAssignmentsTest(unittest.TestCase):
    def setUp(self):
        self.base_path = path.abspath(path.dirname(__file__))
        self.data_dir = path.join(self.base_path, "data/")

    def test_success(self):
        with self.assertRaises(AssertionError):
            get_hole_value_assignments(["a"], "a__one = 3; a__two = 4")

        holes_to_values = get_hole_value_assignments(
            ["a", "b", "c"], "a__one = 3; b__two = 4 c__three = 5")

        self.assertEqual(holes_to_values, {"a": "3", "b": "4", "c": "5"})
