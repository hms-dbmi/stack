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
        if self.options['<app>']:

            # Get the app.
            valid = True
            app = self.options['<app>']

            if not App.check_build_context(app):
                logger.error('({}) Build context is invalid'.format(app))
                valid = False

            if not App.check_docker_images(docker_client, app):
                logger.error('({}) Build images are invalid'.format(app))
                valid = False

            if valid:
                logger.info('({}) Build parameters are valid!'.format(app))

        else:

            # Check all apps.
            valid = True
            apps = App.get_apps()
            for app in apps:
                logger.debug('({}) Checking build context...'.format(app))

                # Check build configs.
                if not App.check_build_context(app):
                    logger.error('({}) Build context is invalid'.format(app))
                    valid = False

                # Check docker images.
                if not App.check_docker_images(docker_client, app):
                    logger.error('({}) Docker images are missing'.format(app))
                    valid = False

            if valid:
                logger.info('All app build parameters are valid')



