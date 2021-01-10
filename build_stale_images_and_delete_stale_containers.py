from pathlib import Path
import yaml
import argparse
import podman_commands
from pathlib import PurePath

# A version of argparse.ArgumentParser, that report errors
# with a non-zero exit code
class WrappedArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(125, "%s: error: %s\n" % (self.prog, message))

def parse_args():
    parser = WrappedArgumentParser(description='Builds podman images locally that need to be rebuilt')
    parser.add_argument("--config", type=str, metavar=('<file-path>'), required=True,
                        help='The config file to load')
    return parser.parse_args()

def load_config(config_filepath):
    with open(config_filepath) as f:
        return yaml.load(f, Loader=yaml.FullLoader)

def build_stale_images(config, config_filepath):
    for image in config['images']:
        image_name = image['name']

        print('[[ Checking Image [%s] ... ]]' % image_name)
        if not podman_commands.need_to_rebuild_image(image_name):
            print('[[ Image [%s] up to date ]]' % image_name)
            continue
        else:
            print('[[ Image [%s] needs rebuild ]]' % image_name)

        build_dir = PurePath(image['directory'])
        if not build_dir.is_absolute():
            build_dir = config_filepath.parent.joinpath(build_dir)

        print('')
        print('[[ Building Image [%s] ... ]]' % image_name)
        print('')
        podman_commands.build_image(build_dir, image_name)
        print('')
        print('[[ Building Image [%s] Complete ]]' % image_name)
        print('')

        print('[[ Pruning Untagged Images ... ]]')
        podman_commands.prune_untagged_images()
        print('[[ Pruning Untagged Images Complete ]]')

def stop_delete_stale_containers(config):
    for container in config['containers']:
        container_name = container['name']
        print('[[ Checking Container [%s] ... ]]' % container_name)
        if not podman_commands.need_to_rebuild_container(container['image'], container_name):
            print('[[ Container [%s] up to date ]]' % container_name)
            continue
        else:
            print('[[ Container [%s] needs rebuild ]]' % container_name)
        print('[[ Stopping container [%s], if exists ]]' % container_name)
        podman_commands.stop_container_if_exists(container_name)
        print('[[ Deleting container [%s], if exists ]]' % container_name)
        podman_commands.remove_container(container_name)

def __main():
    args = parse_args()
    config = load_config(args.config)
    build_stale_images(config, PurePath(args.config))
    stop_delete_stale_containers(config)

__main()
