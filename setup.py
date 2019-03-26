from distutils import log
from pathlib import Path
import os
import subprocess

from setuptools import setup
from setuptools import find_packages
from setuptools.command.build_py import build_py

_PACKAGE_NAME = "chipc"


class BuildByWrapper(build_py):
    """Provides a build_py wrapper to generate parser using chipmunk grammar
    file."""

    def run(self):
        self._generate_parser()
        build_py.run(self)

    def _generate_parser(self):
        """Generates chipmunk grammar parser using chipmunk/stateful_alu.g4
        file. Assumes the user has java binary."""

        alu_filepath = Path(_PACKAGE_NAME, "stateful_alu.g4")
        assert os.access(alu_filepath,
                         os.R_OK), "Can't find grammar file: %s" % alu_filepath

        antlr_jar = Path(_PACKAGE_NAME, "lib", "antlr-4.7.2-complete.jar")
        run_args = [
            "java", "-jar",
            str(antlr_jar), alu_filepath, "-Dlanguage=Python3", "-visitor",
            "-package", "chipc"
        ]

        existing_files = set(os.listdir(_PACKAGE_NAME))
        subprocess.run(run_args, check=True)
        generated_files = set(os.listdir(_PACKAGE_NAME)) - existing_files
        # Check whether Antlr actually generated any file.
        assert generated_files, "Antlr4 failed to generate Parser/Lexer."
        log.info("Antlr generated files: %s" % ", ".join(
            [str(f) for f in generated_files]))


setup(
    name=_PACKAGE_NAME,
    version="0.1",
    description="A switch code generator based on end-to-end program " +
    "synthesis.",
    url="https://github.com/anirudhSK/chipmunk",
    author="Chipmunk Contributors",
    packages=find_packages(exclude=["tests*", "*.interp", "*.tokens"]),
    # This will let setuptools to copy ver what"s listed in MANIFEST.in
    include_package_data=True,
    cmdclass={"build_py": BuildByWrapper},
    entry_points={"console_scripts": ["chipmunk=chipc.chipmunk:run_main"]})
