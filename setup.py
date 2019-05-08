"""Packaging settings."""


from codecs import open
from os.path import abspath, dirname, join
from subprocess import call

from setuptools import Command, find_packages, setup

from stack import __version__


this_dir = abspath(dirname(__file__))
with open(join(this_dir, 'README.md'), encoding='utf-8') as file:
    long_description = file.read()


def read(f):
    return open(f, 'r', encoding='utf-8').read()


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
    name='hmsdbmitc-stack',
    version=__version__,
    description='A command line program to manage a Docker stack.',
    long_description=long_description,
    url='https://github.com/hms-dbmi/stack.git',
    author='HMS DBMI Tech-core',
    author_email='bryan_larson@hms.harvard.edu',
    license='UNLICENSE',
    classifiers=[
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
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='cli',
    packages=find_packages(exclude=['docs', 'tests*']),
    install_requires=read('requirements.txt').splitlines(),
    test_requires=read('requirements.test.txt').splitlines(),
    extras_require={
    },
    entry_points={
        'console_scripts': [
            'stack=stack.cli:main',
        ],
    },
    cmdclass={'test': RunTests},
)
