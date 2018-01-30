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
            app = self.options['<app>']

            if App.check_build_context(app):
                logger.info('({}) Build context is valid'.format(app))

            else:
                logger.critical('({}) Build context is invalid'.format(app))
                return

            if App.check_docker_images(docker_client, app):
                logger.info('({}) Build images are valid'.format(app))

            else:
                logger.critical('({}) Build images are invalid'.format(app))
                return

        else:

            # Check all apps.
            valid = True
            apps = App.get_apps()
            for app in apps:
                logger.debug('({}) Checking build context...'.format(app))

                # Check build configs.
                if not App.check_build_context(app):
                    logger.critical('({}) Build context is invalid'.format(app))
                    valid = False

                # Check docker images.
                if not App.check_docker_images(docker_client, app):
                    logger.critical('({}) Docker images are missing'.format(app))
                    valid = False

                logger.info('({}) Build context is valid!'.format(app))

            if valid:
                logger.info('All stack.app build parameters are valid')



