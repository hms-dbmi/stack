"""The reup command."""

import sys
import os
import subprocess
import docker

from .base import Base
from stack.app import App
from stack.app import Stack

import logging
logger = logging.getLogger('stack')


class Reup(Base):

    def run(self):

        # Get a docker client.
        docker_client = docker.from_env()

        # Get options.
        clean = self.options['--clean']
        app = self.options['<app>']

        # Check for clean.
        if clean:

            # Clean and fetch.
            App.clean_images(docker_client, app)

            # Build it.
            App.build(app)

        # Capture and redirect output.
        subprocess.call(['docker-compose', 'kill', app])
        subprocess.call(['docker-compose', 'rm', '-f', '-v', app])

        # Run the pre-up hook, if any
        Stack.hook('pre-up', app)

        subprocess.call(['docker-compose', 'up', '--no-start', app])
        subprocess.call(['docker-compose', 'start', app])

        # Run the post-up hook, if any
        Stack.hook('post-up', app)
