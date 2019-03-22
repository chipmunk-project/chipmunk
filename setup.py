import subprocess
import sys
import os
import shutil

from setuptools import setup
from setuptools import find_packages
from setuptools.command.install_lib import install_lib


class InstallWrapper(install_lib):
    def run(self):
        install_lib.run(self)
        self._generate_parser()

    def _generate_parser(self):
        cmd = 'antlr'
        if sys.platform.startswith('linux'):
            cmd += '4'
        assert shutil.which(
            cmd) is not None, ("Can't find %s executable." % cmd)

        alu_filepath = os.path.join(self.install_dir, "chipmunk/stateful_alu.g4")

        assert os.access(alu_filepath, os.R_OK), "Can't find grammar file: %s" % alu_filepath

        run_args = "antlr %s -Dlanguage=Python3 -visitor -package chipmunk" % alu_filepath
        subprocess.run(run_args, shell=True, capture_output=True, check=True)


setup(
    name='chipmunk',
    version='0.1',
    description='A switch code generator based on end-to-end program ' +
    'synthesis.',
    url='https://github.com/anirudhSK/chipmunk',
    author='Chipmunk Contributors',
    packages=find_packages(exclude=["tests*"]),
    include_package_data=True,
    cmdclass={'install_lib': InstallWrapper})
