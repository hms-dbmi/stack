"""The up command."""

import sys
import subprocess
import docker
import os
import configparser

from .base import Base
from stack.app import App
from stack.app import Stack

import logging
logger = logging.getLogger('stack')


class Up(Base):

    def run(self):

        # Check for clean.
        if self.options['--clean']:

            # Get the docker client.
            docker_client = docker.from_env()

            # Run the pre-clean hook, if any
            Stack.hook('pre-clean')

            App.clean_images(docker_client)

            # Run the post-clean hook, if any
            Stack.hook('post-clean')

        # Build the command.
        command = ['docker-compose', 'up']

        # Check for the daemon flag.
        if self.options['-d']:
            command.append('-d')

        # Run the pre-build hook, if any
        Stack.hook('pre-up')

        # Capture and redirect output.
        logger.debug('Running docker-compose up...')
        with open('docker-compose.log', 'w') as f:
            process = subprocess.Popen(command, stdout=subprocess.PIPE)
            for c in iter(lambda: process.stdout.read(1), ''):
                sys.stdout.write(c)
                f.write(c)

        # Run the pre-build hook, if any
        Stack.hook('post-up')


