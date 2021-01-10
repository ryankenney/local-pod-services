import subprocess
import re
import json
from enum import Enum
from datetime import datetime

# # A version of argparse.ArgumentParser, that report errors
# # with a non-zero exit code
# class WrappedArgumentParser(argparse.ArgumentParser):
#     def error(self, message):
#         self.exit(125, "%s: error: %s\n" % (self.prog, message))

# class Action(Enum):
#     BUILD_IMAGE = 1
#     STOP_CONTAINER_IF_NEEDS_REBUILD = 2
#     REBUILD_RESTART_CONTAINER = 3

# def parse_args():
#     actions = ', '.join(list(map(lambda a: a.name, list(Action))))
#     parser = WrappedArgumentParser(description='A wrapper script for containers managed by podman.')
#     parser.add_argument("--action", type=str, metavar=('<action>'), required=True,
#                         help='The main action to execute. Valid values: %s' % actions)
#     parser.add_argument("--image", type=str, metavar=('<image-name>'), required=False,
#                         help='The image to build or use.')
#     parser.add_argument("--container", type=str, metavar=('<container-name>'), required=False,
#                         help='The container to affect.')
#     config = parser.parse_args()
#     # Validate action string
#     Action(config.action)
#     return config

def container_exists(container_name):
    proc = subprocess.run( \
        ['podman', 'ps', '--all', '--format', '{{.Names}}'], \
        check=True, universal_newlines=True, stdout=subprocess.PIPE)
    containers = proc.stdout.strip()
    return (container_name in set(containers.splitlines()))

def image_exists(image_name):
    # We filter by reference name, but this only does substring matching,
    # so we look for complete matches in the result.
    proc = subprocess.run( \
        ['podman', 'image', 'ls', '--filter=reference=' + image_name, '--format', '{{json}}'], \
        check=True, universal_newlines=True, stdout=subprocess.PIPE)
    # Search for exact image name match
    images = json.loads(proc.stdout)
    for image in images:
        if image_name in set(image['Names']):
            return True
    return False

def prune_untagged_images():
    subprocess.run( \
        ['podman', 'image', 'prune', '-f'], \
        check=True, universal_newlines=True)

def container_running(container_name):
    proc = subprocess.run( \
        ['podman', 'ps', '--format', '{{.Names}}'], \
        check=True, universal_newlines=True, stdout=subprocess.PIPE)
    containers = proc.stdout.strip()
    return (container_name in set(containers.splitlines()))

def get_image_hash(image_name):
    proc = subprocess.run( \
        ['podman', 'image', 'inspect', '--format', 'table {{.Id}}', image_name], \
        check=True, universal_newlines=True, stdout=subprocess.PIPE)
    hash = proc.stdout.strip()
    if not re.compile(r'^\w+$').match(hash):
        raise Exception('Hash output not recognized: %s' % hash)
    return hash

def get_container_image_hash(container_name):

    print(['podman', 'inspect', container_name, '--format', '{{.Image}}'])

    proc = subprocess.run( \
        ['podman', 'inspect', container_name, '--format', '{{.Image}}'], \
        check=True, universal_newlines=True, stdout=subprocess.PIPE)
    hash = proc.stdout.strip()
    if not re.compile(r'^\w+$').match(hash):
        raise Exception('Hash output not recognized: %s' % hash)
    return hash

def image_time_to_secs(image_time):
    match = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6})\d* (\+0000) UTC$').match(image_time)
    if not match:
        raise Exception(('Image time format [%s] does not match expected. ' + \
            'Time conversion logic needs review.') % image_time)
    # Trim nanoseconds to microseconds and drop the text-based timezone
    image_time = '%s %s' % (match.group(1), match.group(2))
    dateobj = datetime.strptime(image_time, '%Y-%m-%d %H:%M:%S.%f %z')
    return dateobj.timestamp()

def get_image_time_secs(image_name):
    proc = subprocess.run( \
        ['podman', 'image', 'inspect', image_name, '--format', '{{.Created}}'], \
        check=True, universal_newlines=True, stdout=subprocess.PIPE)
    image_timestamp = proc.stdout.strip()
    return image_time_to_secs(image_timestamp)

def need_to_rebuild_image(image_name):
    DURATION_24H_SECS = 60*60*24
    if not image_exists(image_name):
        print('Image [%s] does not exist' % image_name)
        return True
    else:
        print('Image [%s] exists' % image_name)
    image_secs = get_image_time_secs(image_name)
    now_secs = datetime.now().timestamp()
    if now_secs - image_secs >= DURATION_24H_SECS:
        print('Image [%s] more than 24 hours old' % image_name)
        return True
    else:
        print('Image [%s] less than 24 hours old' % image_name)
    return False

def need_to_rebuild_container(image_name, container_name):
    if not container_exists(container_name):
        print('Container [%s] does not exist' % container_name)
        return True
    else:
        print('Container [%s] exists' % container_name)
    if not container_running(container_name):
        print('Container [%s] is not running' % container_name)
        return True
    else:
        print('Container [%s] is running' % container_name)
    image_hash = get_image_hash(image_name)
    print('Image [%s] has hash [%s]' % (image_name, image_hash))
    container_hash = get_container_image_hash(container_name)
    print('Container [%s] has hash [%s]' % (container_name, container_hash))
    if container_hash != image_hash:
        print('Container needs rebuild from latest image')
        return True
    print('Container running latest image, no action necessary')
    return False

def build_image(source_directory, image_name):
    # --pull-always: I believe this ensures that the base image
    # is the latest version from dockerhub, regardless of whether
    # or not we already have the same docker tag locally,
    # and that a failure to pull will result in an error
    # (the ideal if we want to always be sure we have the true
    # latest release).
    # --pull-always: We always want a fresh build. This is a no-op right now.
    # but specifying it ensure's it's true.
    # Issue #1: I need to test/prove this.
    # Issue #2: Doing this at the build level means a lot more requests
    #           to dockerhub (for the same base image),
    #           which get us throttled by their new policy.
    subprocess.run( \
        ['podman', 'build', '--no-cache', '--pull-always', '-t', image_name, '.'], \
        cwd=str(source_directory), check=True, universal_newlines=True)

def run_container(image_name, container_name, run_args):
    command = ['podman', 'run', '--rm', '--name', container_name, '--log-driver', 'journald']
    command.extend(run_args)
    command.append(image_name)
    subprocess.run(command, check=True, universal_newlines=True)

def stop_container_if_exists(container_name):
    if not container_exists(container_name):
        return
    subprocess.run(['podman', 'stop', container_name], check=True, universal_newlines=True)

def remove_container(container_name):
    subprocess.run(['podman', 'rm', '-i', container_name], check=True, universal_newlines=True)

