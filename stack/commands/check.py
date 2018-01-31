"""The check command."""

import docker

from .base import Base
from stack.app import App

import logging
logger = logging.getLogger('stack')


class Check(Base):

    def run(self):

        # Get the docker client.
        docker_client = docker.from_env()

        # Determine the app.
        app = self.options['<app>']
        if app is not None:

            # Check it.
            if App.check(docker_client, app):
                logger.info('({}) Is valid and ready to go!'.format(app))

        else:

            # Check all apps.
            stack_valid = True
            apps = App.get_apps()
            for app in apps:

                # Check the app.
                if App.check(docker_client, app):
                    logger.info('({}) Is valid and ready to go!'.format(app))

                else:
                    stack_valid = False

            if stack_valid:
                logger.info('The Stack is valid and ready to go!')
            else:
                logger.critical('Stack invalid! Ensure all paths and images are correct and try again')



