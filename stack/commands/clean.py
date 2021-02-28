"""The clean command."""

import docker

from stack.commands.base import Base
from stack.app import App

import logging

logger = logging.getLogger("stack")


class Clean(Base):
    def run(self):

        # Get the docker client.
        docker_client = docker.from_env()

        # Determine the app.
        app = self.options["<app>"]

        # Purge database
        App.purge_data(docker_client, app)
