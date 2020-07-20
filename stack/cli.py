"""
dbmisvc-stack

Usage:
  dbmisvc-stack init [<app>] [-v | --verbose]
  dbmisvc-stack check [<app>] [-v | --verbose]
  dbmisvc-stack build [<app>] [--clean] [-v | --verbose]
  dbmisvc-stack test [-v | --verbose]
  dbmisvc-stack up [-d] [--clean] [--flags=<flags>] [-v | --verbose]
  dbmisvc-stack down [--clean] [--flags=<flags>] [-v | --verbose]
  dbmisvc-stack reup [-c|--clean] [-p|--purge] [-r|--recreate] [<app>] [-d] [--flags=<flags>] [-v | --verbose]
  dbmisvc-stack shell [--sh] <app> [-v | --verbose]
  dbmisvc-stack logs <app> [--minutes=<minutes>] [--lines=<lines>] [-F|--follow]
  dbmisvc-stack clone <app> <branch> [-v | --verbose]
  dbmisvc-stack status [<app>] [-v | --verbose]
  dbmisvc-stack checkout <app> [-b] <branch> [-v | --verbose]
  dbmisvc-stack update [<app>] [-v | --verbose]
  dbmisvc-stack push <app> <branch> [--squash] [-v | --verbose]
  dbmisvc-stack pull <app> <branch> [--squash] [-v | --verbose]
  dbmisvc-stack packages [<package>] [-v | --verbose]
  dbmisvc-stack secrets [-f | --force] [-v | --verbose]
  dbmisvc-stack -h | --help
  dbmisvc-stack --version
  dbmisvc-stack -v | --verbose

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
  -F,--follow                       Follow the logs in the current terminal
  -f,--force                        Force the command to run, possibly overwriting existing resources
  -r,--recreate                     Docker will recreate dependent services


Examples:
  dbmisvc-stack reup --clean app

Help:
  For help using this tool, please open an issue on the Github repository:
  https://github.com/hms-dbmi/stack.git
"""  # noqa: E501


from inspect import getmembers, isclass

from docopt import docopt
import logging
from colorlog import ColoredFormatter

from stack import VERSION
from stack.app import Stack


def setup_logger(options):
    """Return a logger with a default ColoredFormatter."""
    formatter = ColoredFormatter(
        "%(log_color)s%(message)-8s%(reset)s",
        datefmt=None,
        reset=True,
        log_colors={
            "INFO": "white",
            "DEBUG": "cyan",
            "WARNING": "yellow",
            "ERROR": "purple",
            "CRITICAL": "bold_red",
        },
    )

    logger = logging.getLogger("stack")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Check level
    if options["--verbose"]:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    return logger


def main():
    """Main CLI entrypoint."""
    import os
    from stack import commands
    from stack.commands.base import Base

    options = docopt(__doc__, version=VERSION)

    # Setup logging.
    logger = setup_logger(options)

    # Make sure we are in a valid location
    if not Stack.check_stack(os.getcwd()):
        logger.critical("The Stack is invalid, cannot run...")
        return

    # Here we'll try to dynamically match the command the user is trying to run
    # with a pre-defined command class we've already created.
    for (k, v) in options.items():
        if hasattr(commands, k) and v:
            module = getattr(commands, k)
            _commands = getmembers(
                module, lambda cmd: isclass(cmd) and issubclass(cmd, Base)
            )
            command = [command[1] for command in _commands if command[0] != "Base"][0]
            command = command(options)
            command.run()
