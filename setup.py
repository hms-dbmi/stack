"""Packaging settings."""


from codecs import open
from os.path import abspath, dirname, join
from subprocess import call

from setuptools import Command, find_packages, setup

from stack import __version__


readme = join(abspath(dirname(__file__)), 'README.md')
try:
    import pypandoc
    long_description = pypandoc.convert(readme, 'rst')
except(IOError, ImportError):
    long_description = open(readme).read()


class RunTests(Command):
    """Run all tests."""
    description = 'run tests'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        """Run all tests!"""
        errno = call(['py.test', '--cov=stack', '--cov-report=term-missing'])
        raise SystemExit(errno)


setup(
    name = 'stack',
    version = __version__,
    description = 'A command line program to manage a Docker stack.',
    long_description = long_description,
    url = 'https://github.com/hms-dbmi/stack.git',
    author = 'HMS DBMI Tech-core',
    author_email = 'bryan_larson@hms.harvard.edu',
    license = 'UNLICENSE',
    classifiers = [
        'Intended Audience :: Developers',
        'Topic :: Utilities',
        'License :: Public Domain',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    keywords = 'cli',
    packages = find_packages(exclude=['docs', 'tests*']),
    install_requires = ['docopt',
                        'boto3',
                        'docker',
                        'nose',
                        'pyyaml',
                        'selenium',
                        'splinter',
                        'colorlog'],
    extras_require = {
    },
    entry_points = {
        'console_scripts': [
            'stack=stack.cli:main',
        ],
    },
    cmdclass = {'test': RunTests},
)
