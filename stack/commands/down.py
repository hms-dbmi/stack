"""The down command."""

import sys
import subprocess
import docker

from .base import Base
from stack.app import App

import logging
logger = logging.getLogger('stack')


class Down(Base):

    def run(self):

        # Build the command.
        command = ['docker-compose', 'down', '--volumes']

        # Capture and redirect output.
        logger.debug('Running docker-compose down...')
        with open('docker-compose.log', 'w') as f:
            process = subprocess.Popen(command, stdout=subprocess.PIPE)
            for c in iter(lambda: process.stdout.read(1), ''):
                sys.stdout.write(c)
                f.write(c)

