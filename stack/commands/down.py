"""The down command."""

import sys
import subprocess
import docker

from .base import Base
from stack.app import Stack

import logging
logger = logging.getLogger('stack')


class Down(Base):

    def run(self):

        # Build the command.
        command = ['docker-compose', 'down']

        # Check for flags
        if self.options.get('<flags>'):

            # Split them, append the '--' and add them to the command
            for flag in self.options.get('<flags>').split(','):
                command.append('-{}'.format(flag) if len(flag) == 1 else '--{}'.format(flag))

        # Check for cleaning up
        if self.options['--clean'] and '-v' not in command and '--volumes' not in command:
            command.append('--volumes')

        # Capture and redirect output.
        logger.debug('Running docker-compose down...')
        Stack.run(command)

