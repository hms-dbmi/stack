# Stack

#### A program for running a stack of Docker services

## Purpose

This is a program to provide some convenience wrappers around common tasks
when developing with a Dockerized stack of micro-services. The program aims
to simplify some of the management of a local stack and make it easier to
develop on an entire stack whilst running and testing it.

The application depends on configurations defined in the base `stack.yml`
file for the applications that will be built.

## App Properties

- `repository`: This should specify the URL to the app's git repository.
- `branch`: The particular branch to checkout when cloning the repo.
- `packages`: Any packages listed for the Stack that this app depends on

## Package Properties

- `name`: The name of the package to be used when installing from PyPi/mirror
- `path`: The path to the directory containing the package source
- `build`: The build command Stack should execute when updating the package

## Setup

0. Create your Python virtualenv and install requirements:
`pip install -r requirements.txt`

1. First step is to place any needed overrides in the `overrides/{APP}`
directory. These files are what will be used to build the image that
will be run in the stack. Typically they closely mirror the files
the app uses in its production environment, but with small tweaks to
run locally and to interface with other local apps. This directory
must contain a `Dockerfile` if the app is to run off a built image.

2. The next step is to clone all needed repositories into the `apps` directory.
`stack` includes some convenience commands for managing the subtree
repositories. Do this with one command by running `stack init`.
See below for further details on repository management.

3. Next, configure secrets. Ensure the secrets configuration is accurate in `stack.yml`. Specifically, ensure your
AWS profile is set to the account that contains this Stack's secrets. Secrets must be fetched and persisted locally
as `.env`, do this by running `stack secrets [--force]`.

4. The next step is to make sure the `docker-compose.yml` file is fully
and accurately filled out to include the apps and their configurations.
This includes any volumes needed to mount the app's source within the
container. This allows for file changes to update the services
automatically so changes can be tested immediately. Verify current setup
by running `stack check`.

5. Lastly, update the hook scripts with any extra bits of code
needed to run the stack. Whether you need to collect npm
dependencies after cloning a repo or you need a database to
be cleared when cleaning an app, this is where custom functionality
should live.

## Stack Commands

To check stack configurations and to ensure volume paths are correct,
required images exist, etc:

> `stack check [<app>]`

Not passing an app will iterate through all services specified in the
`docker-compose.yml` file and check all configurations.

Run the initialize command to clone all needed repositories to their
respective branches:

> `stack init`

Most applications will require sensitive secrets to function and stack assumes those will be saved in AWS Secrets Manager. Be sure
the correct configuration is set in `stack.yml` and remote secrets will be fetched and persisted to `.env` which is automatically
used by docker-compose as a source of environment variables for services.

To pull those secrets down from AWS by running (pass `-f` to overwrite existing `.env` file):

> `stack secrets [-f]`

To get the stack going, run the following command (pass `-d` to daemonize
the process):

> `stack up [-d]`

If a container needs to be rebuilt for some reason (updated requirements, etc),
run the following command (app is the key of the service in your `docker-compose.yml`):

> `stack reup <app> [--clean]`

You could instead shell into the needed container and run the requirements
update command there:

> `stack shell <app> [-sh]`

Stack defaults to trying to open a bash shell, but you can default to
sh if bash is not available.

You can also check logs on a container with a couple constraints to more
easily find the relevant logs:

> `stack logs <app> [--minutes=n] [--lines=n] [-f]`

You can specify how many minutes in the past to start the log retrieval
or the number of lines to get. You can also pass the `-f` flag to follow
the logs as the container runs.

This will stop and remove the container, and then start it up again. The clean
flag will purge the existing container image and rebuild before running again.

To bring the stack down, run the following:

> `stack down`

This merely wraps `docker-compose down --volumes` and brings the stack down
and removes any left-over data volumes.

> `stack packages [package]`

This command will attempt to build and upload the package to the PyPi
mirror for use by the apps in the Stack. Any apps that were marked
as dependent on this package will trigger a reinstall of that
package automatically when a new build is successfully registered with
the local PyPi mirror.


## Git Subtree Helper Commands

Stack apps are included as git subtrees. Commands were added to Stack to
wrap and simplify the commands needed to work with these repositories.

Before cloning, make sure the app exists in the `docker-compose.yml` file
and has the required configurations, namely the repository URL. The current
`docker-compose.yml` file illustrates how to do this with the current set
of apps.

**Git subtree commands will not run with pending changes in the working
directory. Commit all changes before running subtree commands.**

To clone an existing repo into the `apps` directory:

> `stack clone <app> <branch>`

This will clone the repo as a subtree in the `apps` directory
(default: {PROJECT_ROOT}/apps). If the app is already present in the
`apps` directory, that copy will be removed and the specified branch
will be cloned in its place.

To pull remote changes into the local branch, use the `pull` command:

> `stack pull <app> <branch> [--squash]`

All commits pulled are added to the stack repository so squashing
the incoming commits keeps history tidy.

To create a new branch for a specified app:

> `stack checkout <app> -b <branch>`

This splits the subtree into the new specified branch. Commit changes
as usual for the entire stack repository. Once an update is ready to push,
run the push command as usual:

> `stack push <app> <branch> [--squash]`

This will collect commits relevant to the particular subtree and push those
to origin for the new branch. The `--squash` command will collapse those
commits into a single commit.

To get back to the base branch, checkout the branch as usual:

> `stack checkout <app> <branch>`

This removes the subtree entirely, and clones the specified branch in
its place.

