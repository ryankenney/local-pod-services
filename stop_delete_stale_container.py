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
    parser = WrappedArgumentParser(description='Recreates and starts a podman container')
    parser.add_argument("--config", type=str, metavar=('<file-path>'), required=True,
                        help='The config file to load')
    return parser.parse_args()

def load_config(config_filepath):
    with open(config_filepath) as f:
        return yaml.load(f, Loader=yaml.FullLoader)

def stop_delete_stale_container(config, config_filepath):
    container_name = config['name']

    print('[[ Checking Container [%s] ... ]]' % container_name)

    if not podman_commands.need_to_rebuild_container(config['image'], container_name):
        print('[[ Container [%s] up to date ]]' % container_name)
        return
    else:
        print('[[ Container [%s] needs rebuild ]]' % container_name)

    podman_commands.stop_container_if_exists(container_name)
    podman_commands.remove_container(container_name)

def __main():
    args = parse_args()
    config = load_config(args.config)
    stop_delete_stale_container(config, PurePath(args.config))

__main()

