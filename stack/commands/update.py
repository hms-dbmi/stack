"""The checkout command."""

import sys
import os
import subprocess

from .base import Base
from stack.app import App
from stack.app import Stack

import logging
logger = logging.getLogger('stack')


class Update(Base):

    def run(self):

        # Create a list of apps to update
        apps = App.get_apps()

        # Get the app.
        app = self.options.get('<app>')
        if app:
            apps = [app]

        # Filter out apps without repository details
        apps = [app for app in apps if App.get_repo_branch(app)]

        # Ensure no local changes
        if Stack.run(['git', 'diff-index', '--name-status', '--exit-code', 'HEAD']):
            logger.error('Current working copy has changes, cannot update app repositories')
            exit(1)

        logger.info('Will update {}'.format(', '.join(apps)))

        # Iterate and update
        for app in apps:

            # Get the repo URL
            repo_url = App.get_repo_url(app)
            branch = App.get_repo_branch(app)
            if repo_url is None or branch is None:
                logger.error('({}) No repository URL and/or branch specified...'.format(app))
                continue

            # Determine the path to the app directory
            apps_dir = os.path.relpath(Stack.get_config('apps-directory'))
            subdir = os.path.join(apps_dir, app)

            # Check for pre-checkout hook
            Stack.hook('pre-checkout', app, [os.path.realpath(subdir)])

            # Build the command
            command = ['git', 'subtree', 'add', '--prefix={}'.format(subdir), repo_url, branch, '--squash']

            # Remove the current subtree.
            Stack.run(['git', 'rm', '-rf', subdir])
            Stack.run(['rm', '-rf', subdir])
            Stack.run(['git', 'commit', '-m', '"Stack op: Removing subtree {} for cloning branch {}"'.format(app, branch)])

            # Run the command.
            Stack.run(command)

            # Check for post-checkout hook
            Stack.hook('post-checkout', app, [os.path.realpath(subdir)])


