import subprocess
import sys
import os
import shutil

from setuptools import setup
from setuptools import find_packages
from setuptools.command.build_py import build_py


class BuildByWrapper(build_py):
    """Provides a build_py wrapper to generate parser using chipmunk grammar
    file."""

    def run(self):
        self._generate_parser()
        build_py.run(self)

    def _generate_parser(self):
        """Generates chipmunk grammar parser using chipmunk/stateful_alu.g4
        file. It first checks for existence for antlr (mac OS) or antlr4 (Linux
        like) command."""
        cmd = 'antlr'
        if sys.platform.startswith('linux'):
            cmd += '4'
        assert shutil.which(cmd) is not None, (
            "Can't find %s executable." % cmd)

        # TODO: Instead of hardcoding chipc package name, get it
        # programmatically.
        alu_filepath = "chipc/stateful_alu.g4"
        assert os.access(alu_filepath,
                         os.R_OK), "Can't find grammar file: %s" % alu_filepath

        run_args = [
            cmd, alu_filepath, '-Dlanguage=Python3', '-visitor', '-package',
            'chipc'
        ]
        subprocess.run(run_args, capture_output=True, check=True)


setup(
    name='chipc',
    version='0.1',
    description='A switch code generator based on end-to-end program ' +
    'synthesis.',
    url='https://github.com/anirudhSK/chipmunk',
    author='Chipmunk Contributors',
    packages=find_packages(exclude=["tests*", "*.interp", "*.tokens"]),
    # This will let setuptools to copy ver what's listed in MANIFEST.in
    include_package_data=True,
    cmdclass={'build_py': BuildByWrapper},
    entry_points={
        'console_scripts': ['chipmunk=chipmunk.chipmunk:run_main']
    })
