"""The up command."""

import sys
import subprocess
import docker

from .base import Base
from stack.app import App
from stack.app import Stack

import logging
logger = logging.getLogger('stack')


class Up(Base):

    def run(self):

        # Get the docker client.
        docker_client = docker.from_env()

        # Check it.
        if not App.check(docker_client):
            logger.critical('Stack is invalid! Ensure all paths and images are correct and try again')
            return

        # Check for clean.
        if self.options['--clean']:

            App.clean_images(docker_client)

        # Iterate through built apps
        for app in App.get_built_apps():
            App.build(app)

        # Build the command.
        command = ['docker-compose', 'up']

        # Check for the daemon flag.
        if self.options['-d']:
            command.append('-d')

        # Check for flags
        if self.options.get('<flags>'):

            # Split them, append the '--' and add them to the command
            for flag in self.options.get('<flags>').split(','):
                command.append('-{}'.format(flag) if len(flag) == 1 else '--{}'.format(flag))

        # Run the pre-build hook, if any
        Stack.hook('pre-up')

        # Capture and redirect output.
        logger.debug('Running docker-compose up...')

        Stack.run(command)

        # Run the pre-build hook, if any
        Stack.hook('post-up')


