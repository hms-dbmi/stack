"""The clone command."""

import sys
import os
import subprocess

from .base import Base
from stack.app import App
from stack.app import Stack

import logging
logger = logging.getLogger('stack')


class Clone(Base):

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
        if os.path.exists(subdir):
            logger.error('({}) A repository already exists, use "stack checkout" to change branches'.format(app))
            return

        # Build the command
        command = ['git', 'subtree', 'add', '--prefix={}'.format(subdir), repo_url, branch, '--squash']

        # Check for pre-clone hook
        Stack.hook('pre-clone', app, [os.path.realpath(subdir)])

        # Run the command.
        return_code = Stack.run(command)

        # Check for post-clone hook
        if return_code == 0:
            Stack.hook('post-clone', app, [os.path.realpath(subdir)])


