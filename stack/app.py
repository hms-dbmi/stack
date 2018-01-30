import os
import docker
import re
from docker import errors
import subprocess
import yaml

import logging
logger = logging.getLogger('stack')


class Stack:

    @staticmethod
    def get_config(property):
        """
        Get a configuration property for the stack, defined in {PROJECT_ROOT}/stack.yml
        :param property: The key of the property to retrieve.
        :return:
        """

        # Get the path to the config.
        root_dir = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))
        stack_file = os.path.join(root_dir, 'stack.yml')

        # Parse the yaml.
        if os.path.exists(stack_file):
            with open(stack_file, 'r') as f:
                config = yaml.load(f)

                # Get the value.
                value = config.get(property)
                if value is not None:

                    return value

                else:
                    logger.error('Stack property \'{}\' does not exist!'.format(property))
                    return None

        else:
            logger.error('Stack configuration file does not exist!')
            return None

    @staticmethod
    def hook(step, app='stack', arguments=None):
        """
        Check for a script for the given hook and runs it.
        :param step: The name of the event, and the name of the hook script
        :param app: The app, if any, the event is for.
        :param arguments: Any additional arguments related to the event to be passed to the hook
        :return: None
        """

        # Get the path to the hooks directory.
        hooks_dir = os.path.join(os.path.realpath(os.path.dirname(os.path.dirname(__file__))), 'hooks')
        script_file = os.path.join(hooks_dir, '{}.py'.format(step))

        # Check it.
        logger.debug('Looking for hook: {}'.format(script_file))
        if os.path.exists(script_file):

            # Build the command
            command = ['python', script_file]

            # Add the app, if any.
            if app is not None:
                command.append(app)

            if arguments is not None:
                command.extend(arguments)

            # Call the file.
            logger.debug('Running hook: {}'.format(command))
            process = subprocess.Popen(command, stdout=subprocess.PIPE)
            for line in iter(lambda: process.stdout.readline(), ''):
                logger.debug('({}) {}: {}'.format(app, step, line))

        else:
            logger.error('(stack) No script exists for hook \'{}\''.format(step))

    @staticmethod
    def get_stack_root():
        return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


class App:

    @staticmethod
    def get_build_dir(app):

        # Build the path to the apps folders
        apps_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'overrides')
        return os.path.join(apps_dir, app)

    @staticmethod
    def check_running(docker_client, app):

        # Get the container name.
        name = App.get_container_name(app)

        # Skip if not container name is specified.
        if not name:
            logger.debug('({}) Skipping app status check'.format(app))
            return True

        # Fetch it.
        try:
            logger.debug('({}) Attempting to fetch container'.format(app))

            container = docker_client.containers.get(name)

            logger.info('({}) Container found with status "{}"'.format(app, container.status))

            return container.status == 'running'

        except docker.errors.NotFound:
            logger.warning('({}) Container is not running, ensure all containers are running'.format(app))

        return False

    @staticmethod
    def clean_images(docker_client, app=None):

        # Determine what to clean
        apps = [app] if app is not None else App.get_apps()

        # Iterate through built apps
        for app_to_clean in apps:

            # Ensure it's a built app.
            if App.get_app_config(app_to_clean, 'build') is not None:

                if App.check_docker_images(docker_client, app_to_clean, external=False):

                    # Get the docker image name.
                    image_name = App._get_image_name(app_to_clean)

                    # Remove it.
                    docker_client.images.remove(image=image_name, force=True)

                    # Log.
                    logger.debug('({}) Docker images cleaned successfully'.format(app_to_clean))

            else:

                # Log.
                logger.debug('({}) Not a built app, no need to clean images'.format(app_to_clean))

    @staticmethod
    def check_docker_images(docker_client, app, external=False):

        # Check the testing image.
        image = App._get_image_name(app)

        # Check type
        if not external:

            # Ensure it exists locally.
            try:
                docker_client.images.get(image)
                return True

            except docker.errors.ImageNotFound:
                logger.warning(
                    '({}) Docker image "{}" not found, will need to build...'.format(app, image))
                pass

        else:

            try:
                images = docker_client.images.search(image)
                for remote_image in images:
                    if remote_image['name'] == image:
                        return True

            except (docker.errors.ImageNotFound or docker.errors.APIError):
                logger.warning(
                    '({}) Docker image "{}" not found anywhere'.format(app, image))
                pass

        return False

    @staticmethod
    def check_build_context(app):

        # Get the path to the override directory
        context_dir = App.get_app_config(app, 'build')
        if context_dir is None:
            return True

        # Append to project root
        path = os.path.normpath(os.path.join(Stack.get_stack_root(), context_dir))

        # Set flags to check the context.
        exists = os.path.exists(path)
        dockerfile = os.path.exists(os.path.join(context_dir, 'Dockerfile'))

        return exists and dockerfile

    @staticmethod
    def _get_config():

        # Get the path to the config.
        apps_config = os.path.join(Stack.get_stack_root(), 'docker-compose.yml')

        # Parse the yaml.
        if os.path.exists(apps_config):
            with open(apps_config, 'r') as f:
                return yaml.load(f)

    @staticmethod
    def get_app_config(app, config):
        try:
            # Get the config.
            config_dict = App._get_config()

            return config_dict['services'][app][config]

        except KeyError as e:
            logger.warning('No "{}" property found for app "{}"'.format(config, app))

            return None

    @staticmethod
    def _get_app_test_config(app, config):
        try:
            # Get the config.
            config_dict = App._get_config()

            return config_dict['services'][app]['labels'][config]

        except KeyError as e:
            return None

    @staticmethod
    def get_apps():

        # Get the config.
        config = App._get_config()

        # Return the apps.
        return config['services'].keys()

    # NEED #
    @staticmethod
    def get_repo_url(app):
        repository = App._get_app_test_config(app, 'repository')

        # Expand if necessary.
        return repository

    @staticmethod
    def get_requirements_file(app):
        requirements_file = App._get_app_test_config(app, 'requirements_file')

        # Append it to the project root.
        path = os.path.normpath(os.path.join(Stack.get_stack_root(), requirements_file))

        # Expand if necessary.
        return os.path.realpath(path) if path else None

    @staticmethod
    def get_container_name(app):
        return App.get_app_config(app, 'container_name')

    @staticmethod
    def _get_image_name(app):
        return App.get_app_config(app, 'image')

    @staticmethod
    def get_value_from_logs(docker_client, app, regex, lines='all'):

        try:
            # Get the scireg container.
            container = docker_client.containers.get(App.get_container_name(app))

            # Get the logs.
            logs = container.logs(tail=lines)

            # Find the links.
            matches = re.search(regex, logs)
            if matches:

                # Get the value.
                link = matches.group(1)
                logger.debug('({}) Found log value: "{}"'.format(app, link))

                return link
            else:
                logger.error('({}) Could not find value for pattern "{}"'.format(app, regex))

                return None
        except Exception as e:
            logger.exception('({}) Getting log value failed: {}'.format(app, e))

            return None

    @staticmethod
    def run_command(docker_client, app, cmd):

        try:
            # Get the container.
            container = docker_client.container.get(App.get_container_name(app))

            # Flush the database.
            return container.exec_run(cmd)

        except docker.errors.APIError as e:
            logger.exception('({}) Error while running command: {}'.format(app, e))
        except docker.errors.NotFound:
            logger.error('({}) Container could not be found for running command'.format(app))

        return None






