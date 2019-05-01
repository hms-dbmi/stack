"""The packages command."""

import docker
import os

from .base import Base
from stack.app import App
from stack.app import Stack

import logging
logger = logging.getLogger('stack')


class Packages(Base):

    def run(self):

        # Ensure we have an index specified
        index = Stack.get_config('index')
        if not index:
            logger.error('Stack package index not specified, cannot proceed')
            exit(1)

        # Get the package, if specified
        if self.options['<package>']:
            packages = [self.options['<package>']]
        else:
            packages = [package['name'] for package in Stack.get_config('packages')]

        # Process each package
        for package in packages:

            # Update the package
            if self.update(package):
                logger.info('Package "{}" was updated successfully'.format(package))

                # Update services
                self.update_apps(package)

            else:
                logger.error('Error: Could not update package')
                exit(1)

    @staticmethod
    def update(package):

        try:
            # Get devpi index details
            port = App.get_external_port('devpi', '3141')
            index_url = 'http://localhost:{}/root/public/'.format(port)

            # Get the description
            config = App.get_packages_stack_config(package)

            # Get password
            password = App.get_config('devpi', 'environment').get('DEVPI_PASSWORD')

            # Get the location
            path = os.path.abspath(config['path'])
            dists = os.path.join(path, 'dist', '*')

            # Build the package
            Stack.run(config.get('build'), cwd=path)

            # Upload
            cmd = ['twine', 'upload', dists, '--repository-url', index_url, '--skip-existing',
                   '-u', 'root', '-p', password]

            # Run it and make sure it was successful
            return Stack.run(cmd) == 0

        except Exception as e:
            logger.exception('Error updating package: {}'.format(e), exc_info=True)
            return False

    @staticmethod
    def update_apps(package):

        # Find all services listing this package
        for app, config in Stack.get_config('apps').items():

            try:
                # Check packages
                if config.get('packages') and package in config.get('packages'):

                    # Get the docker client.
                    docker_client = docker.from_env()

                    # Determine the app.
                    if App.check_running(docker_client, app):
                        logger.info('App "{}" depends on "{}", reinstalling...'.format(app, package))

                        # Build the uninstall command
                        uninstall = ['docker-compose', 'exec', app, 'pip', 'uninstall', '-y', package]

                        # Execute a shell.
                        code = Stack.run(uninstall)
                        if code == 0:
                            logger.info('    ... uninstalled ...')

                            # Build the install command
                            install = ['docker-compose', 'exec', app, 'pip', 'install', package]

                            # Execute a shell.
                            code = Stack.run(install)
                            if code == 0:
                                logger.info('        ... reinstall succeeded!')

                            else:
                                logger.error('    .... failed with exit code: {}'.format(code))

                        else:
                            logger.error('    .... failed with exit code: {}'.format(code))

                    else:
                        logger.error('    .... App {} is not running, cannot update'.format(app))

            except Exception as e:
                logger.exception('Error reinstalling package for {}: {}'.format(app, e), exc_info=True)
