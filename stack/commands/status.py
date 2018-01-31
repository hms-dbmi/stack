"""The status command."""

import docker

from .base import Base
from stack.app import App
from stack.app import Stack

import logging
logger = logging.getLogger('stack')


class Status(Base):

    def run(self):

        # Get the docker client.
        docker_client = docker.from_env()

        # Get the app.
        app = self.options['<app>']
        if app is not None:

            # Check run status
            logger.info('({}) Status: {}'.format(app, App.get_status(docker_client, app)))

        else:

            # Get all app statuses
            for app in App.get_apps():
                logger.info('({}) Status: {}'.format(app, App.get_status(docker_client, app)))
