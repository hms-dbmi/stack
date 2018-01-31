import os
import docker
import re
from docker import errors
import subprocess
import yaml
import sys

import logging
logger = logging.getLogger('stack')


class Stack:

    @staticmethod
    def check_stack(cwd):
        """
        Checks to ensure the Stack is valid at the current directory
        :param cwd: Current working directory
        :type cwd: String
        :return: Whether the Stack is valid or not
        :rtype: Boolean
        """

        # Default to valid.
        valid = True

        # Check for required docker-compose file
        if not os.path.exists(os.path.join(cwd, 'docker-compose.yml')) and \
                not os.path.exists(os.path.join(cwd, 'docker-compose.yaml')):
            logger.critical('ERROR: docker-compose.yml is missing!')
            valid = False

        if not os.path.exists(os.path.join(cwd, 'stack.yaml')) and \
                not os.path.exists(os.path.join(cwd, 'stack.yml')):
            logger.critical('ERROR: stack.yml is missing!')
            valid = False

        return valid

    @staticmethod
    def get_config(property):
        """
        Get a configuration property for the stack, defined in {PROJECT_ROOT}/stack.yml
        :param property: The key of the property to retrieve.
        :return:
        """

        # Get the path to the config.
        stack_file = os.path.join(Stack.get_stack_root(), 'stack.yml')

        # Parse the yaml.
        if os.path.exists(stack_file):
            with open(stack_file, 'r') as f:
                config = yaml.load(f)

                # Get the value.
                value = config['stack'].get(property)
                if value is not None:

                    return value

                else:
                    logger.error('Stack property \'{}\' does not exist!'.format(property))
                    return None

        else:
            logger.error('Stack configuration file does not exist!')
            return None

    @staticmethod
    def get_app_config(app, property):

        try:
            # Get the config.
            apps_dict = Stack.get_config('apps')

            return apps_dict[app][property]

        except KeyError:
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
        hooks_dir = os.path.join(Stack.get_stack_root(), 'hooks')
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
        return os.getcwd()


class App:

    @staticmethod
    def check(docker_client, app=None):

        if app is not None:

            # Get the app.
            valid = True

            # Check if built.
            if App.get_build_dir(app) is not None:

                if not App.check_build_context(app):
                    logger.critical('({}) Build context is invalid'.format(app))
                    valid = False

            else:

                if not App.check_docker_images(docker_client, app, external=True):
                    logger.critical('({}) Docker image does not exist in the Docker registry'.format(app))
                    valid = False

            return valid

        else:

            # Check all apps.
            valid = True
            for app in App.get_apps():

                valid = valid and App.check(docker_client, app)

            return valid

    @staticmethod
    def get_built_apps():

        # Return apps with the 'build' property
        built_apps = []
        for app in App.get_apps():

            if App.get_build_dir(app) is not None:
                built_apps.append(app)

        return built_apps

    @staticmethod
    def build(app):

        # Check context and build.
        if App.check_build_context(app):

            # Run the pre-build hook, if any
            Stack.hook('pre-build')

            # Capture and redirect output.
            logger.debug('Running "docker-compose build {} --no-cache"'.format(app))
            with open('docker-compose.log', 'w') as f:
                process = subprocess.Popen(['docker-compose', 'build', app, '--no-cache'], stdout=subprocess.PIPE)
                for c in iter(lambda: process.stdout.read(1), ''):
                    sys.stdout.write(c)
                    f.write(c)

            # Run the pre-build hook, if any
            Stack.hook('post-build')
        else:
            logger.error('({}) Build context is invalid, cannot build...'.format(app))

    @staticmethod
    def get_build_dir(app):
        return App.get_config(app, 'build')

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
            if App.get_config(app_to_clean, 'build') is not None:

                if App.check_docker_images(docker_client, app_to_clean, external=False):

                    # Get the docker image name.
                    image_name = App.get_image_name(app_to_clean)

                    # Run the pre-clean hook, if any
                    Stack.hook('pre-clean')

                    # Remove it.
                    docker_client.images.remove(image=image_name, force=True)

                    # Run the post-clean hook, if any
                    Stack.hook('post-clean')

                    # Log.
                    logger.debug('({}) Docker images cleaned successfully'.format(app_to_clean))

            else:

                # Log.
                logger.debug('({}) Not a built app, no need to clean images'.format(app_to_clean))

    @staticmethod
    def check_docker_images(docker_client, app, external=False):

        # Check the testing image.
        image = App.get_image_name(app)

        # Ensure it exists locally.
        try:
            logger.debug('({}) Looking for docker image "{}" locally'.format(app, image))
            docker_client.images.get(image)
            return True

        except docker.errors.ImageNotFound:

            if not external:
                logger.warning(
                    '({}) Docker image "{}" not found, will need to build...'.format(app, image))
                return False

            else:
                # Try to find it externally
                try:
                    logger.debug('({}) Looking for docker image "{}" in the Docker registry'.format(app, image))
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
        context_dir = App.get_config(app, 'build')
        if context_dir is None:
            return True

        # Append to project root
        path = os.path.normpath(os.path.join(Stack.get_stack_root(), context_dir))

        # Set flags to check the context.
        if not os.path.exists(path):
            logger.error('({}) The build directory "{}" does not exist'.format(app, path))
            return False

        if not os.path.exists(os.path.join(context_dir, 'Dockerfile')):
            logger.error('({}) The build directory "{}" does not contain a Dockerfile'.format(app, path))
            return False

        # Get volumes
        valid = True
        volumes = App.get_config(app, 'volumes')
        for volume in volumes:

            # Split it.
            segments = volume.split(':')

            # See if it exists.
            path = os.path.normpath(os.path.join(Stack.get_stack_root(), segments[0]))
            if not os.path.exists(path):
                logger.error('({}) Volume "{}" does not exist, ensure paths are correct'.format(app, path))
                valid = False

        return valid

    @staticmethod
    def read_config():

        # Get the path to the config.
        apps_config = os.path.join(Stack.get_stack_root(), 'docker-compose.yml')

        # Parse the yaml.
        if os.path.exists(apps_config):
            with open(apps_config, 'r') as f:
                return yaml.load(f)

    @staticmethod
    def get_config(app, config):
        try:
            # Get the config.
            config_dict = App.read_config()

            return config_dict['services'][app][config]

        except KeyError:
            logger.debug('({}) No property "{}" found'.format(app, config))
            return None

    @staticmethod
    def get_app_stack_config(app, config):

        # Try the stack config
        config = Stack.get_app_config(app, config)
        if config is not None:
            return config

        try:
            # Get the config.
            config_dict = App.read_config()

            return config_dict['services'][app]['labels'][config]

        except KeyError:
            logger.debug('({}) No property "{}" found'.format(app, config))
            return None

    @staticmethod
    def get_apps():

        # Get the config.
        config = App.read_config()

        # Return the apps.
        return config['services'].keys()

    # NEED #
    @staticmethod
    def get_repo_url(app):
        repository = App.get_app_stack_config(app, 'repository')

        # Expand if necessary.
        return repository

    @staticmethod
    def get_repo_branch(app):
        branch = App.get_app_stack_config(app, 'branch')

        # Expand if necessary.
        return branch

    @staticmethod
    def get_container_name(app):
        return App.get_config(app, 'container_name')

    @staticmethod
    def get_image_name(app):
        return App.get_config(app, 'image')

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

            # Run the command
            return container.exec_run(cmd)

        except docker.errors.APIError as e:
            logger.exception('({}) Error while running command: {}'.format(app, e))
        except docker.errors.NotFound:
            logger.error('({}) Container could not be found for running command'.format(app))

        return None

    @staticmethod
    def get_status(docker_client, app):

        # Get the container name.
        name = App.get_container_name(app)

        # Skip if not container name is specified.
        if not name:
            logger.debug('({}) Skipping app status check, no container name...'.format(app))
            return 'N/A'

        # Fetch it.
        try:
            container = docker_client.containers.get(name)

            return container.status

        except docker.errors.NotFound:
            logger.debug('({}) Container could not be found'.format(app))
            return 'Not found'
