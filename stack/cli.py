"""
stack

Usage:
  stack init [<app>] [-v | --verbose]
  stack check [<app>] [-v | --verbose]
  stack build [<app>] [--clean] [-v | --verbose]
  stack test [-v | --verbose]
  stack up [-d] [--clean] [--flags=<flags>] [-v | --verbose]
  stack down [--clean] [--flags=<flags>] [-v | --verbose]
  stack reup [-c|--clean] [-p|--purge] <app> [--flags=<flags>] [-v | --verbose]
  stack shell [--sh] <app> [-v | --verbose]
  stack logs <app> [--minutes=<minutes>] [--lines=<lines>] [-f|--follow]
  stack clone <app> <branch> [-v | --verbose]
  stack status [<app>] [-v | --verbose]
  stack checkout <app> [-b] <branch> [-v | --verbose]
  stack update [<app>] [-v | --verbose]
  stack push <app> <branch> [--squash] [-v | --verbose]
  stack pull <app> <branch> [--squash] [-v | --verbose]
  stack packages [<package>] [-v | --verbose]
  stack -h | --help
  stack --version
  stack -v | --verbose

Options:
  -h --help                         Show this screen.
  --version                         Show version.
  -v,--verbose                      Show logging outputs during commands
  -c,--clean                        Re-fetch project files and re-build Docker images
  -p,--purge                        Clear any database related to the application
  --flags=<flags>                   Additional flags to add to the docker-compose command (e.g. 'flag_a,flag_b')
  --sh                              Use the basic shell if Bash isn't available
  --minutes=<minutes>               How many minutes in the past to display logs from
  --lines=<lines>                   How many lines from the tail of the logs to display
  -f,--follow                       Follow the logs in the current terminal


Examples:
  stack reup --clean app

Help:
  For help using this tool, please open an issue on the Github repository:
  https://github.com/hms-dbmi/stack.git
"""


from inspect import getmembers, isclass

from docopt import docopt
import logging
from colorlog import ColoredFormatter

from . import __version__ as VERSION
from stack.commands import base
from stack.app import Stack


def setup_logger(options):
    """Return a logger with a default ColoredFormatter."""
    formatter = ColoredFormatter(
        "%(log_color)s%(message)-8s%(reset)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'bold_red',
        }
    )

    logger = logging.getLogger('stack')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Check level
    if options['--verbose']:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    return logger


def main():
    """Main CLI entrypoint."""
    import os
    import stack.commands

    options = docopt(__doc__, version=VERSION)

    # Setup logging.
    logger = setup_logger(options)

    # Make sure we are in a valid location
    if not Stack.check_stack(os.getcwd()):
        logger.critical('The Stack is invalid, cannot run...')
        return

    # Here we'll try to dynamically match the command the user is trying to run
    # with a pre-defined command class we've already created.
    for (k, v) in options.items(): 
        if hasattr(stack.commands, k) and v:
            module = getattr(stack.commands, k)
            stack.commands = getmembers(module, lambda cmd: isclass(cmd) and issubclass(cmd, base.Base))
            command = [command[1] for command in stack.commands if command[0] != 'Base'][0]
            command = command(options)
            command.run()
