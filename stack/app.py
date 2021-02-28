import os
import threading
from docker import errors as docker_errors
import re
import subprocess
import yaml
import select
from logging import DEBUG, INFO

import logging

logger = logging.getLogger("stack")
stdout_logger = logging.getLogger("stdout")


class LogPipe(threading.Thread):
    def __init__(self, level):
        """Setup the object with a logger and a loglevel
        and start the thread
        """
        threading.Thread.__init__(self)
        self.daemon = False
        self.level = level
        self.fdRead, self.fdWrite = os.pipe()
        self.pipeReader = os.fdopen(self.fdRead)
        self.start()

    def fileno(self):
        """Return the write file descriptor of the pipe"""
        return self.fdWrite

    def run(self):
        """Run the thread, logging everything."""
        for line in iter(self.pipeReader.readline, ""):
            logging.log(self.level, line.strip("\n"))

        self.pipeReader.close()

    def close(self):
        """Close the write end of the pipe."""
        os.close(self.fdWrite)


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
        if not os.path.exists(
            os.path.join(cwd, "docker-compose.yml")
        ) and not os.path.exists(os.path.join(cwd, "docker-compose.yaml")):
            logger.critical("ERROR: docker-compose.yml is missing!")
            valid = False

        if not os.path.exists(os.path.join(cwd, "stack.yaml")) and not os.path.exists(
            os.path.join(cwd, "stack.yml")
        ):
            logger.critical("ERROR: stack.yml is missing!")
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
        stack_file = os.path.join(Stack.get_stack_root(), "stack.yml")

        # Parse the yaml.
        if os.path.exists(stack_file):
            with open(stack_file, "r") as f:
                config = yaml.load(f, Loader=yaml.FullLoader)

                # Get the value.
                value = config["stack"].get(property)
                if value is not None:

                    return value

                else:
                    logger.error("Stack property '{}' does not exist!".format(property))
                    return None

        else:
            logger.error("Stack configuration file does not exist!")
            return None

    @staticmethod
    def get_app_config(app, property):

        try:
            # Get the config.
            apps_dict = Stack.get_config("apps")

            return apps_dict[app][property]

        except KeyError:
            return None

    @staticmethod
    def get_secrets_config(property):

        try:
            # Get the config.
            secrets_dict = Stack.get_config("secrets")

            return secrets_dict[property]

        except KeyError:
            return None

    @staticmethod
    def hook(step, app="stack", arguments=None):
        """
        Check for a script for the given hook and runs it.
        :param step: The name of the event, and the name of the hook script
        :param app: The app, if any, the event is for.
        :param arguments: Any additional arguments related to the event to
         be passed to the hook
        :return: None
        """

        # Get the path to the hooks directory.
        hooks_dir = os.path.join(Stack.get_stack_root(), "hooks")
        script_file = os.path.join(hooks_dir, "{}.py".format(step))

        # Check it.
        logger.debug("(stack) Looking for hook: {}".format(script_file))
        if os.path.exists(script_file):

            # Build the command
            command = ["python", script_file]

            # Add the app, if any.
            if app is not None:
                command.append(app)

            if arguments is not None:
                command.extend(arguments)

            # Call the file.
            logger.debug("(stack) Running hook: {}".format(command))
            Stack.run(command)

        else:
            logger.debug("(stack) No script exists for hook '{}'".format(step))

    @staticmethod
    def get_stack_root():
        return os.getcwd()

    @staticmethod
    def run(args, **kwargs):
        """
        Runs subprocess.call and sends stdout and stderr to stdout and stderr
        """
        subprocess.call(args, **kwargs)

    @staticmethod
    def run_redirect(args, **kwargs):
        """
        Variant of subprocess.call that accepts a logger instead of stdout/stderr,
        and logs stdout messages via logger.debug and stderr messages via
        logger.error.
        """
        child = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs
        )

        # Docker-compose uses stderr for console output
        log_level = {child.stdout: INFO, child.stderr: DEBUG}

        def check_io():
            ready_to_read = select.select([child.stdout, child.stderr], [], [], 1000)[0]
            for io in ready_to_read:
                line = io.readline()
                if len(line) > 0:
                    logger.log(log_level[io], "(docker-compose) " + line[:-1].decode())

        # keep checking stdout/stderr until the child exits
        while child.poll() is None:
            check_io()

        check_io()  # check again to catch anything after the process exits

        return child.wait()

    @staticmethod
    def get_database_container():
        """
        Queries the stack and attempts to find the container that is being used
        for databases.

        :return: A tuple of database type and container name
        :rtype: str, str
        """
        # Set a list of supported databases
        databases = ["mysql", "postgres", "mariadb"]

        # Check hardcoded specification in stack.yml
        if Stack.get_config("database-container"):

            # Get needed props
            database = Stack.get_config("database-container")["database"]
            container = Stack.get_config("database-container")["name"]
            if database not in databases:
                raise NotImplementedError(
                    "Database '{}' is not supported".format(database)
                )

            return database, container

        # Check primary DB types
        for database in databases:

            # Determine which app provides the database
            for container in App.get_apps():
                if App.get_config(container, "image") and database in App.get_config(
                    container, "image"
                ):
                    return database, container

    @staticmethod
    def _recreate_postgres_database(docker_client, container, database):
        """
        Creates commands to recreate a database within a Postgres container and
        executes them.

        :param docker_client: The current Docker client
        :type docker_client: docker.client
        :param container: The name of the container running the Postgres database
        :type container: str
        :param database: The name of the database to recreate
        :type database: str
        :returns: Whether the operation succeeded or not
        :rtype: bool
        """
        raise NotImplementedError("Postgres support has not been implemented")

    @staticmethod
    def _recreate_mariadb_database(docker_client, container, database):
        """
        Creates commands to recreate a database within a MariaDB container and
        executes them. This just proxies to MySQL method.

        :param docker_client: The current Docker client
        :type docker_client: docker.client
        :param container: The name of the container running the MariaDB database
        :type container: str
        :param database: The name of the database to recreate
        :type database: str
        :returns: Whether the operation succeeded or not
        :rtype: bool
        """
        return App._recreate_mysql_database(docker_client, container, database)

    @staticmethod
    def _recreate_mysql_database(docker_client, container, database):
        """
        Creates commands to recreate a database within a MySQL container and
        executes them.

        :param docker_client: The current Docker client
        :type docker_client: docker.client
        :param container: The name of the container running the MySQL database
        :type container: str
        :param database: The name of the database to recreate
        :type database: str
        :returns: Whether the operation succeeded or not
        :rtype: bool
        """
        # Connect.
        username = "root"
        password = App.get_config(container, "environment").get("MYSQL_ROOT_PASSWORD")

        # Build the command to drop database and run it
        command = "mysqladmin -u{} -p{} -f drop {}".format(username, password, database)
        exit_code, output = App.run_command(docker_client, container, command)

        # Check result
        if exit_code:
            logger.error(
                "({}) Purge operation to drop database failed: {} - {}".format(
                    container, exit_code, output
                )
            )
            return False
        else:
            logger.debug(
                "({}) Drop database: {} - {}".format(container, exit_code, output)
            )

        # Build the command to create empty database and run it
        command = "mysqladmin -u{} -p{} create {}".format(username, password, database)
        exit_code, output = App.run_command(docker_client, container, command)

        # Check result
        if exit_code:
            logger.error(
                "({}) Purge operation to create database failed: {} - {}".format(
                    container, exit_code, output
                )
            )
            return False
        else:
            logger.debug(
                "({}) Create database: {} - {}".format(container, exit_code, output)
            )

        # Build the command to flush privileges and run it
        command = "mysqladmin -u{} -p{} flush-privileges".format(username, password)
        exit_code, output = App.run_command(docker_client, container, command)

        # Check result
        if exit_code:
            logger.error(
                "({}) Purge operation to flush privileges failed: {} - {}".format(
                    container, exit_code, output
                )
            )
            return False
        else:
            logger.debug(
                "({}) Flush privileges: {} - {}".format(container, exit_code, output)
            )

        return True


class App:
    @staticmethod
    def check(docker_client, app=None):

        if app is not None:

            # Get the app.
            valid = True

            # Check if built.
            if App.get_build_dir(app) is not None:

                if not App.check_build_context(app):
                    logger.critical("({}) Build context is invalid".format(app))
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
            Stack.hook("pre-build", app)

            # Capture and redirect output.
            logger.debug('(stack) Running "docker-compose build {}"'.format(app))

            Stack.run(["docker-compose", "build", app])

            # Run the pre-build hook, if any
            Stack.hook("post-build", app)
        else:
            logger.error("({}) Build context is invalid, cannot build...".format(app))

    @staticmethod
    def get_build_dir(app):

        # Get the path to the override directory
        build_config = App.get_config(app, "build")

        # Check for a dict
        if build_config and type(build_config) is dict:
            return build_config.get("context")
        else:
            return build_config

    @staticmethod
    def check_running(docker_client, app):

        # Get the container name.
        name = App.get_container_name(app)

        # Skip if not container name is specified.
        if not name:
            logger.debug("({}) Skipping app status check".format(app))
            return True

        # Fetch it.
        try:
            logger.debug("({}) Attempting to fetch container".format(app))

            container = docker_client.containers.get(name)

            logger.info(
                "({}) Container found with status '{}'".format(app, container.status)
            )

            return container.status == "running"

        except docker_errors.NotFound:
            logger.warning(
                "({}) Container is not running, ensure all containers"
                " are running".format(app)
            )

        return False

    @staticmethod
    def clean_images(docker_client, app=None):

        # Determine what to clean
        apps = [app] if app is not None else App.get_apps()

        # Iterate through built apps
        for app_to_clean in apps:

            # Ensure it's a built app.
            if App.get_config(app_to_clean, "build") is not None:

                if App.check_docker_images(docker_client, app_to_clean, external=False):

                    # Get the docker image name.
                    image_name = App.get_image_name(app_to_clean)

                    # Run the pre-clean hook, if any
                    Stack.hook("pre-clean")

                    # Remove it.
                    docker_client.images.remove(image=image_name, force=True)

                    # Run the post-clean hook, if any
                    Stack.hook("post-clean")

                    # Log.
                    logger.debug(
                        "({}) Docker images cleaned successfully".format(app_to_clean)
                    )

            else:

                # Log.
                logger.debug(
                    "({}) Not a built app, no need to clean images".format(app_to_clean)
                )

    @staticmethod
    def check_docker_images(docker_client, app, external=False):

        # Check the testing image.
        image = App.get_image_name(app)

        # Ensure it exists locally.
        try:
            logger.debug(
                "({}) Looking for docker image '{}' locally".format(app, image)
            )
            docker_client.images.get(image)
            return True

        except docker_errors.ImageNotFound:

            if not external:
                logger.warning(
                    "({}) Docker image '{}' not found, will need to build...".format(
                        app, image
                    )
                )
                return False

            else:
                # Try to find it externally
                try:
                    logger.debug(
                        "({}) Looking for docker image '{}' in the Docker"
                        " registry".format(app, image)
                    )
                    images = docker_client.images.search(image)
                    for remote_image in images:
                        if remote_image["name"] == image:
                            return True

                except (docker_errors.ImageNotFound or docker_errors.APIError):
                    logger.warning(
                        "({}) Docker image '{}' not found anywhere".format(app, image)
                    )
                    pass

        return False

    @staticmethod
    def check_build_context(app):

        # Get the path to the override directory
        context_dir = App.get_build_dir(app)
        if context_dir is None:
            return True

        # Append to project root
        path = os.path.normpath(os.path.join(Stack.get_stack_root(), context_dir))

        # Set flags to check the context.
        if not os.path.exists(path):
            logger.error(
                "({}) The build directory '{}' does not exist".format(app, path)
            )
            return False

        if not os.path.exists(os.path.join(context_dir, "Dockerfile")):
            logger.error(
                "({}) The build directory '{}' does not contain a Dockerfile".format(
                    app, path
                )
            )
            return False

        # Get volumes
        valid = True
        if App.get_config(app, "volumes") is not None:
            for volume in App.get_config(app, "volumes"):

                # Split it.
                segments = volume.split(":")

                # Ignore volumes without a host section
                if len(segments) == 1:
                    logger.info(
                        "({}) Volume '{}' is not host-mounted".format(app, volume)
                    )

                elif "/" not in segments[0]:
                    logger.info(
                        "({}) Volume '{}' is a named volume".format(app, volume)
                    )

                else:
                    # See if it exists.
                    path = os.path.normpath(
                        os.path.join(Stack.get_stack_root(), segments[0])
                    )
                    if not os.path.exists(path):
                        logger.error(
                            "({}) Volume '{}' does not exist, ensure paths"
                            " are correct".format(app, path)
                        )
                        valid = False

        return valid

    @staticmethod
    def read_config():

        # Get the path to the config.
        apps_config = os.path.join(Stack.get_stack_root(), "docker-compose.yml")

        # Parse the yaml.
        if os.path.exists(apps_config):
            with open(apps_config, "r") as f:
                return yaml.load(f, Loader=yaml.FullLoader)

    @staticmethod
    def get_config(app, config):
        try:
            # Get the config.
            config_dict = App.read_config()

            return config_dict["services"][app][config]

        except KeyError:
            logger.debug("({}) No property '{}' found".format(app, config))
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

            return config_dict["services"][app]["labels"][config]

        except KeyError:
            logger.debug("({}) No property '{}' found".format(app, config))
            return None

    @staticmethod
    def get_packages_stack_config(package=None):

        # Try the stack config
        packages = Stack.get_config("packages")
        if package is not None:
            return next((p for p in packages if p["name"] == package), None)

        return packages

    @staticmethod
    def get_apps():

        # Get the config.
        config = App.read_config()

        # Return the apps.
        return config["services"].keys()

    # NEED #
    @staticmethod
    def get_repo_url(app):
        repository = App.get_app_stack_config(app, "repository")

        # Expand if necessary.
        return repository

    @staticmethod
    def get_repo_branch(app):
        branch = App.get_app_stack_config(app, "branch")

        # Expand if necessary.
        return branch

    @staticmethod
    def get_container_name(app):
        return App.get_config(app, "container_name")

    @staticmethod
    def get_image_name(app):
        return App.get_config(app, "image")

    @staticmethod
    def get_value_from_logs(docker_client, app, regex, lines="all"):

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
                logger.debug("({}) Found log value: '{}'".format(app, link))

                return link
            else:
                logger.error(
                    "({}) Could not find value for pattern '{}'".format(app, regex)
                )

                return None
        except Exception as e:
            logger.exception("({}) Getting log value failed: {}".format(app, e))

            return None

    @staticmethod
    def run_command(docker_client, app, cmd):

        try:
            # Get the container.
            container = docker_client.containers.get(App.get_container_name(app))

            # Run the command
            return container.exec_run(cmd)

        except docker_errors.NotFound:
            logger.error(
                "({}) Container could not be found for running command".format(app)
            )
        except docker_errors.APIError as e:
            logger.exception("({}) Error while running command: {}".format(app, e))

        return None

    @staticmethod
    def get_status(docker_client, app):

        # Get the container name.
        name = App.get_container_name(app)

        # Skip if not container name is specified.
        if not name:
            logger.debug(
                "({}) Skipping app status check, no container name...".format(app)
            )
            return "N/A"

        # Fetch it.
        try:
            container = docker_client.containers.get(name)

            return container.status

        except docker_errors.NotFound:
            logger.debug("({}) Container could not be found".format(app))
            return "Not found"

    @staticmethod
    def init(app):
        """
        This method prepares a built app by checkout out its code and running
        the necessary scripts
        :param app:
        :type app:
        :return:
        :rtype:
        """

        # Get the repo URL
        repo_url = App.get_repo_url(app)
        repo_branch = App.get_repo_branch(app)

        # Ensure valid values.
        if repo_url is None or repo_branch is None:
            logger.error(
                "({}) Repository URL or branch is not specified,"
                " cannot initialize...".format(app)
            )
            return

        # Determine the path to the app directory
        apps_dir = os.path.relpath(Stack.get_config("apps-directory"))
        subdir = os.path.join(apps_dir, app)

        # Ensure it exists.
        if os.path.exists(subdir):

            # Remove the current subtree.
            Stack.run(["git", "rm", "-rf", subdir])
            Stack.run(["rm", "-rf", subdir])
            Stack.run(
                [
                    "git",
                    "commit",
                    "-m",
                    '"Stack op: Removing subtree {} for cloning branch {}"'.format(
                        app, repo_branch
                    ),
                ]
            )

        # Build the command
        command = [
            "git",
            "subtree",
            "add",
            "--prefix={}".format(subdir),
            repo_url,
            repo_branch,
            "--squash",
        ]

        # Check for pre-clone hook
        Stack.hook("pre-clone", app, [os.path.realpath(subdir)])

        # Run the command.
        return_code = Stack.run(command)

        # Check for post-clone hook
        if return_code == 0:
            Stack.hook("post-clone", app, [os.path.realpath(subdir)])

            logger.debug("({}) App was initialized successfully!".format(app))

        else:
            logger.critical(
                "({}) Something happened to the init process...".format(app)
            )

    @staticmethod
    def get_external_port(app, internal_port):

        # Get ports and find the matching one
        ports = App.get_config(app, "ports")
        if ports:
            for port in ports:
                if ":{}".format(internal_port) in port:
                    return port.split(":")[0]
                elif port == internal_port:
                    return port

        return None

    @staticmethod
    def purge_data(docker_client, app):
        """
        Checks for and purges the database for the given app
        :param docker_client: The Docker client instance
        :type docker_client: Docker.Client
        :param app: The identifier of the app
        :type app: str
        """
        # Check for defined database
        database_name = App.get_app_stack_config(app, "database")
        if not database_name:
            logger.error(
                f"App {app} does not have 'database' defined in stack, cannot proceed"
            )
            return
        else:
            logger.debug("({}) Will purge database '{}'".format(app, database_name))

        # Get database container and type
        database, container = Stack.get_database_container()

        if not container or not database:
            logger.error(
                "({}) Database purge operation failed, could not determine "
                "database container and/or type".format(app)
            )
            return

        # Drop the database.
        logger.warning(
            "({}) Preparing to purge database '{}' from '{}' ({})".format(
                app, database_name, container, database
            )
        )

        # Run it
        method = getattr(Stack, "_recreate_{}_database".format(database))
        success = method(docker_client, container, database_name)

        # Log.
        if success:
            logger.info("({}) Database purged successfully".format(app))
        else:
            logger.error("({}) Database purge operation failed".format(app))
