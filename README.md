Overview
----------------

This is a simple bash-based wrapper for building/launching containers in podman.
It sort of approximates a feature-limited version of docker-compose.

The goals/features include:

* Automatically rebuild all images and containers locally, daily
    * Thus avoiding a fully continuous integration pipeline to ensure the latest software patches
* Manage running containers via systemd
    * Including capturing logs across container builds
* No dependencies other than podman
* Containers running rootless versus the host


Usage
----------------

Define the local images to build daily in a single yaml file
(I like to use `127.0.0.1:0` has my docker registry host to indicate
that it's always built locally--never pulled from Dockerhub.):

Basic Setup
----------------

```
# my-images.yml

images:

- name: '127.0.0.1:0/git-server:latest'
  # Paths are relative to the config file directory, if not absolute
  directory: '../git-server/'

- name: '127.0.0.1:0/web-proxy:latest'
  directory: '/home/user/docker-images/web-proxy'
```

Define a yaml file for each container:

```
# git-server.container.yml

# Container name
name: 'git-server'
# Docker image
image: '127.0.0.1:0/git-server:latest'
# Specify any args to add to the "podman run" command
run_args: ['-v', 'git-repos:/git:rw', '-p', '127.0.0.1:2222:22']
```

Basic Usage
----------------

Run this periodically to rebuild the images that are more
than 24 hours old or don't exist:

```
python3 build_stale_images.py --config my-images.yml
```

Run this periodically to stop/delete a container that is out
of date with their associated images:

```
python3 stop_delete_stale_container.py --config git-server.container.yml 
```

Run this to start the built container in the foreground
(and configure it to re-start on failure,
thus responding to containers  stale containers):

```
python3 start_container.py --config git-server.container.yml
```

