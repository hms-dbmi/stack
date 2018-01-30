"""The checkout command."""

import sys
import os
import subprocess

from .base import Base
from stack.app import App
from stack.app import Stack

import logging
logger = logging.getLogger('stack')


class Checkout(Base):

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

        # Check if new branch.
        if self.options['-b']:

            # Do a split.
            command = ['git', 'subtree', 'split', '--prefix={}'.format(subdir), '--branch', branch]

            subprocess.call(command)

        else:

            # Build the command
            command = ['git', 'subtree', 'add', '--prefix={}'.format(subdir), repo_url, branch, '--squash']

            # Remove the current subtree.
            subprocess.call(['git', 'rm', '-rf', subdir])
            subprocess.call(['git', 'commit', '-m', '"Stack op: Removing subtree {} for cloning branch {}"'.format(app, branch)])

            # Run the command.
            subprocess.call(command)


