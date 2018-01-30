"""The logs command."""

import sys
import subprocess

from .base import Base
from stack.app import App

import logging
logger = logging.getLogger('stack')


class Up(Base):

    def run(self):

        # Check for time constraints.
        if self.options['--minutes']:

            # Build the command.
            command = ['docker', 'logs', '-t', '--since', '{}m'.format(self.options['--minutes'])]

            # Check for follow
            if self.options['--follow']:
                command.append('-f')

            # Add the app.
            container = App.get_container_name(self.options['<app>'])
            command.append(container)

            # Capture and redirect output.
            with open('docker-compose.log', 'w') as f:
                process = subprocess.Popen(command, stdout=subprocess.PIPE)
                for c in iter(lambda: process.stdout.read(1), ''):
                    sys.stdout.write(c)
                    f.write(c)

        else:

            # Build the command.
            command = ['docker-compose', 'logs', '-t']

            # Check for lines.
            if self.options['--lines']:
                command.extend(['--tail', self.options['--lines']])

            # Check for follow
            if self.options['--follow']:
                command.append('-f')

            # Add the app.
            command.append(self.options['<app>'])

            # Capture and redirect output.
            with open('docker-compose.log', 'w') as f:
                process = subprocess.Popen(command, stdout=subprocess.PIPE)
                for c in iter(lambda: process.stdout.read(1), ''):
                    sys.stdout.write(c)
                    f.write(c)

