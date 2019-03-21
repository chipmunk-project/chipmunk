import subprocess
import sys
import os
import shutil

from setuptools import setup
from setuptools import find_packages
from setuptools.command.install import install


setup(
    name='chipmunk',
    version='0.1',
    description='A switch code generator based on end-to-end program ' +
    'synthesis.',
    url='https://github.com/anirudhSK/chipmunk',
    author='Chipmunk Contributors',
    packages=find_packages(exclude=["tests*"]),
    include_package_data=True)
