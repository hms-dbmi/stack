"""Packaging settings."""


from codecs import open
from subprocess import call

from setuptools import Command, find_packages, setup

from stack import (
    __title__,
    __description,
    __author__,
    __author_email__,
    __license__,
    __url__,
    __version__,
)


def read(f):
    return open(f, "r", encoding="utf-8").read()


class RunTests(Command):
    """Run all tests."""

    description = "run tests"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        """Run all tests!"""
        errno = call(["py.test", "--cov=stack", "--cov-report=term-missing"])
        raise SystemExit(errno)


setup(
    name=__title__,
    version=__version__,
    description=__description,
    long_description=read("README.md"),
    url=__url__,
    author=__author__,
    author_email=__author_email__,
    license=__license__,
    classifiers=[
        "Intended Audience :: Developers",
        "Topic :: Utilities",
        "License :: Public Domain",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    keywords="cli",
    packages=find_packages(exclude=["docs", "tests*"]),
    install_requires=read("requirements.txt").splitlines(),
    extras_require={
        "selenium": read("requirements-selenium.txt").splitlines(),
        "test": read("requirements-test.txt").splitlines(),
        "dev": read("requirements-test.txt").splitlines()
        + read("requirements-dev.txt").splitlines()
        + read("requirements-selenium.txt").splitlines(),
    },
    entry_points={"console_scripts": ["dbmisvc-stack=stack.cli:main",],},
    cmdclass={"test": RunTests},
)
