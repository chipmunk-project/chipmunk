"""Simple unit tests for chipmunk."""

import unittest
import glob
from os import path

from chipmunk import Compiler


class ChipmunkCodegenTest(unittest.TestCase):
    """Tests codegen method from chipmunk.Compiler."""

    def test_codegen_with_simple_sketch_for_all_alus(self):
        cwd = path.abspath(path.dirname(__file__))
        for alu in glob.glob(
                path.join(cwd, "../example_alus/*alu")):
            compiler = Compiler(
                path.join(cwd, "../example_specs/simple.sk"), alu, 2, 2,
                "simple", "serial")
            self.assertEqual(compiler.codegen(), 0)


if __name__ == '__main__':
    unittest.main()
