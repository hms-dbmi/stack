"""The status command."""

import sys
import os
import subprocess

from .base import Base
from stack.app import App
from stack.app import Stack

import logging
logger = logging.getLogger('stack')


class Status(Base):

    def run(self):

        # Get the app.
        app = self.options['<app>']

        # Get the repo URL
        repo_url = App.get_repo_url(app)
        if repo_url is None:
            logger.error('({}) No repository URL specified...'.format(app))
            return

        # Determine the path to the app directory
        apps_dir = Stack.get_config('apps-directory')
        subdir = os.path.join(apps_dir, app)

        # Build the command
        command = ['git', 'subrepo', 'status', subdir]

        # Run the command.
        subprocess.call(command)