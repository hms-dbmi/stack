Stack
=========

*A program for running a stack of Docker services*


Purpose
-------

This is a program to provide some convenience wrappers around common tasks
when developing with a Dockerized stack of micro-services. The program aims
to simplify some of the management of a local stack and make it easier to
develop on an entire stack whilst running and testing it.

Stack Usage
-----

1. The first step is to make sure the `docker-compose.yml` file is fully
and accurately filled out to include the apps and their configurations.
This includes any volumes needed to mount the app's source within the
container. This allows for file changes to update the services
automatically so changes can be tested immediately.

2. Second step is to clone all needed repositories into the `apps` directory.
`stack` includes some convenince commands for managing the subtree
repositories. See below for details.

3. The next step is to place any needed overrides in the `overrides/{APP}`
directory. These files are what will be used to build the image that
will be run in the stack. Typically they closely mirror the files
the app uses in its production environment, but with small tweaks to
run locally and to interface with other local apps. This directory
must contain a `Dockerfile` if the app is to run off a built image.

4. Lastly, update the hook scripts with any extra bits of code
needed to run the stack. Whether you need to collect npm
dependencies after cloning a repo or you need a database to
be cleared when cleaning an app, this is where custom functionality
should live.

Stack Commands
-----

To get the stack going, run the following command:

`stack up [-d] [--clean]`

Flags to determine whether to daemonize the processes and whether existing
container images should be purged and rebuilt before running.

If a container needs to be rebuilt for some reason (updated requirements, etc),
run the following command:

`stack reup [--clean]`

This will stop and remove the container, and then start it up again. The clean
flag will purge the existing container image and rebuild before running again.

To bring the stack down, run the following:

`stack down`

This merely wraps `docker-compose down --volumes` and brings the stack down
and removes any left-over data volumes.


App Repos Usage
-----

Stack apps are included as git subtrees. Commands were added to Stack to
wrap and simplify the commands needed to work with these repositories.

Before cloning, make sure the app exists in the `docker-compose.yml` file
and has the required configurations, namely the repository URL. The current
`docker-compose.yml` file illustrates how to do this with the current set
of apps.

To clone an existing repo into the `apps` directory:

`stack clone <app> <branch>`

This will clone the repo as a subtree in the `apps` directory
(default: {PROJECT_ROOT}/apps).

*** TBD ***

