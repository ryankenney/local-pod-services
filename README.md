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


Setup
----------------

Create a single config file (let's call it `config.yml`).

Within the config file, define the local images to build daily
(I like to use `127.0.0.1:0` has my docker registry host to indicate
that it's always built locally--never pulled from Dockerhub.):

```
images:

- name: '127.0.0.1:0/git-server:latest'
  # If not absolute, paths are relative to the config file directory
  directory: '../git-server/'

- name: '127.0.0.1:0/web-proxy:latest'
  directory: '/home/user/docker-images/web-proxy'
```

Within the config file, define the containers:

```
containers:

  # Container name
- name: 'git-server'
  # Docker image to check for updates, which triggers rebuilds
  image: '127.0.0.1:0/git-server:latest'
  # Specify any args to add to the "podman run" command
  run_args: ['-v', 'git-repos:/git:rw', '-p', '2222:22']

- name: 'web-proxy'
  image: '127.0.0.1:0/web-proxy:latest'
  run_args: ['-p', '8443:443']
```

Usage
----------------

Run this periodically to rebuild the images that are more
than 24 hour old and delete containers using a stale image:

```
python3 build_stale_images_and_delete_stale_containers.py --config config.yml
```

Run this to start a container in the foreground:

```
python3 start_container.py --config config.yml --container git-server
```

The latter command should be configured to auto-restart on failure,
thus responding to deleted stale containers.
