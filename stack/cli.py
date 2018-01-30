"""
stack

Usage:
  stack check [<app>]
  stack test
  stack up [-d] [--clean]
  stack down
  stack reup [-c|--clean] <app>
  stack shell [--sh] <app>
  stack logs <app> [--minutes=<minutes>] [--lines=<lines>] [-f|--follow]
  stack clone <app> <branch>
  stack status <app>
  stack checkout <app> [-b] <branch>
  stack push <app> <branch> [--squash]
  stack pull <app> <branch> [--squash]
  stack -h | --help
  stack --version

Options:
  -h --help                         Show this screen.
  --version                         Show version.
  -c,--clean                        Re-fetch project files and re-build Docker images
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


def setup_logger():
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
    logger.setLevel(logging.DEBUG)

    return logger


def main():
    """Main CLI entrypoint."""
    import stack.commands

    options = docopt(__doc__, version=VERSION)

    # Setup logging.
    setup_logger()

    # Here we'll try to dynamically match the command the user is trying to run
    # with a pre-defined command class we've already created.
    for (k, v) in options.items(): 
        if hasattr(stack.commands, k) and v:
            module = getattr(stack.commands, k)
            stack.commands = getmembers(module, lambda cmd: isclass(cmd) and issubclass(cmd, base.Base))
            command = [command[1] for command in stack.commands if command[0] != 'Base'][0]
            command = command(options)
            command.run()
