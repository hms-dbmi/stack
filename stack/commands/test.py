"""The test command."""

import docker

from .base import Base
from stack.app import App
from stack.app import Stack

import logging
logger = logging.getLogger('stack')


class Test(Base):

    def run(self):

        # Get a docker client.
        docker_client = docker.from_env()

        # Check all the build parameters.
        apps = App.get_apps()
        for app in apps:

            # Check images.
            if not App.check_docker_images(docker_client, app):
                logger.error('({}) Container image does not exist, build and try again...'.format(app))
                return

            # Ensure it is running.
            if not App.check_running(docker_client, app):
                logger.error('({}) Container is not running, ensure all containers are started...'.format(app))
                return

        # Capture and redirect output.
        Stack.run(['nosetests', '-s', '-v'])
