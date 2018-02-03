"""The pull command."""

import sys
import os
import subprocess

from .base import Base
from stack.app import App
from stack.app import Stack

import logging
logger = logging.getLogger('stack')


class Pull(Base):

    def run(self):

        # Get the app.
        app = self.options['<app>']
        branch = self.options['<branch>']

        # Get the repo URL
        repo_url = App.get_repo_url(app)
        if repo_url is None:
            logger.error('({}) No repository URL specified...'.format(app))
            return

        # Determine the path to the app directory
        apps_dir = os.path.relpath(Stack.get_config('apps-directory'))
        subdir = os.path.join(apps_dir, app)

        # Ensure it exists.
        if not os.path.exists(subdir):
            logger.error('({}) No repository at {}, run "stack clone" command first'.format(app))
            return

        # Build the command
        command = ['git', 'subtree', 'pull', '--prefix={}'.format(subdir), repo_url, branch]

        # Check for a squash.
        if self.options.get('--squash'):
            command.append('--squash')

        # Run the command.
        Stack.run(command)


