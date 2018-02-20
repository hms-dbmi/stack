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

        # Check if new branch.
        if self.options['-b']:

            # Ensure it exists.
            if not os.path.exists(subdir):
                logger.error('({}) This repository does not exist yet, run "stack clone" command first'.format(app, subdir))
                return

            # Do a split.
            command = ['git', 'subtree', 'split', '--prefix={}'.format(subdir), '--branch', branch]

            Stack.run(command)

        else:

            # Build the command
            command = ['git', 'subtree', 'add', '--prefix={}'.format(subdir), repo_url, branch, '--squash']

            # Remove the current subtree.
            Stack.run(['git', 'rm', '-rf', subdir])
            Stack.run(['rm', '-rf', subdir])
            Stack.run(['git', 'commit', '-m', '"Stack op: Removing subtree {} for cloning branch {}"'.format(app, branch)])

            # Run the command.
            Stack.run(command)


