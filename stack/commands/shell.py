"""The shell command."""

import docker
import subprocess

from .base import Base
from stack.app import App

import logging
logger = logging.getLogger('stack')


class Shell(Base):

    def run(self):

        # Check which shell.
        shell = '/bin/sh' if self.options['--sh'] else '/bin/bash'

        # Get the docker client.
        docker_client = docker.from_env()

        # Determine the app.
        app = self.options['<app>']
        if App.check_running(docker_client, app):

            # Execute a shell.
            subprocess.call(['docker-compose', 'exec', app, shell])
