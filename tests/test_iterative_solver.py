import unittest
from os import path

from chipc import iterative_solver

BASE_PATH = path.abspath(path.dirname(__file__))
DATA_DIR = path.join(BASE_PATH, "data/")
ALU_DIR = path.join(BASE_PATH, "../example_alus/")
SPEC_DIR = path.join(BASE_PATH, "../example_specs/")
TRANSFORM_DIR = path.join(BASE_PATH, "../example_transforms/")


class IterativeSolverTest(unittest.TestCase):
    def test_simple_2_2_raw_cex_mode(self):
        self.assertEqual(
            0,
            iterative_solver.main([
                "iterative_solver",
                path.join(SPEC_DIR, "simple.sk"),
                path.join(ALU_DIR, "raw.stateful_alu"), "2", "2"]),
        )

    def test_simple_2_2_raw_hole_elimination_mode(self):
        self.assertEqual(
            0,
            iterative_solver.main([
                "iterative_solver", path.join(SPEC_DIR, "simple.sk"),
                path.join(ALU_DIR, "raw.stateful_alu"), "2", "2",
                "--hole-elimination"]),
        )

    def test_sampling_revised_2_2_raw_cex_mode(self):
        self.assertEqual(
            1,
            iterative_solver.main([
                "iterative_solver",
                path.join(SPEC_DIR, "sampling_revised.sk"),
                path.join(ALU_DIR, "raw.stateful_alu"), "2", "2"]),
        )


if __name__ == '__main__':
    unittest.main()
