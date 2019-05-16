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

        # Check for stack or app
        if app:

            # Check for clean.
            if clean:

                # Clean and fetch.
                App.clean_images(docker_client, app)

                # Build it.
                App.build(app)

            # Capture and redirect output.
            Stack.run(['docker-compose', 'kill', app])
            Stack.run(['docker-compose', 'rm', '-f', '-v', app])

            # Run the pre-up hook, if any
            Stack.hook('pre-up', app)

            # Build the  up command
            up = ['docker-compose', 'up', '--no-start']

            # Check for purge
            if self.options['--purge']:

                # Confirm
                if self.yes_no('This will remove all app data, continue?'):
                    logger.warning('({}) Database will be purged!'.format(app))

                    # Process it
                    App.purge_data(app)
            else:
                logger.info('({}) Database will not be purged'.format(app))

            # Check for flags
            if self.options.get('--flags'):

                # Split them
                flags = self.options.get('--flags').split(',')

                # Don't add no-start twice
                if 'no-start' in flags:
                    flags.remove('no-start')

                # Split them, append the '--' and add them to the command
                for flag in flags:
                    up.append('-{}'.format(flag) if len(flag) == 1 else '--{}'.format(flag))

            # Add the app
            up.append(app)

            Stack.run(up)
            Stack.run(['docker-compose', 'start', app])

            # Run the post-up hook, if any
            Stack.hook('post-up', app)

        else:

            # Check for clean.
            if clean and self.yes_no('Clean: Rebuild all app images?'):

                # Clean and fetch.
                for app in App.get_apps():
                    if self.yes_no('({}) Rebuild app image?'):
                        logger.info('({}) Rebuilding image...'.format(app))

                        # Rebuild images
                        App.clean_images(docker_client, app)

            # Build and run stack down
            down_command = ['stack', 'down']
            if clean:
                down_command.append('--clean')

            Stack.run(down_command)

            # Run the pre-up hook, if any
            Stack.hook('pre-up')

            # Build and run stack up
            up_command = ['stack', 'up']
            if self.options['-d']:
                up_command.append('-d')

            Stack.run(up_command)

            # Run the pre-up hook, if any
            Stack.hook('post-up')
