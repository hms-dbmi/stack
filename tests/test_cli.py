"""Tests for our main ppm CLI module."""


import subprocess
from unittest import TestCase

from stack import __version__


class TestHelp(TestCase):
    def test_returns_usage_information(self):
        process = subprocess.run(
            ["stack", "-h"], check=True, stdout=subprocess.PIPE, universal_newlines=True
        )
        output = process.stdout
        self.assertTrue("Usage:" in output)

        process = subprocess.run(
            ["stack", "--help"],
            check=True,
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )
        output = process.stdout
        self.assertTrue("Usage:" in output)


class TestVersion(TestCase):
    def test_returns_version_information(self):
        process = subprocess.run(
            ["stack", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )
        output = process.stdout
        self.assertEqual(output.strip(), __version__)
