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
    parser = WrappedArgumentParser(description='Starts a podman container in the foreground')
    parser.add_argument("--config", type=str, metavar=('<file-path>'), required=True,
                        help='The config file to load')
    parser.add_argument("--container", type=str, metavar=('<container-name>'), required=True,
                        help='The name of the container defined in the config file to run')
    return parser.parse_args()

def load_config(config_filepath):
    with open(config_filepath) as f:
        return yaml.load(f, Loader=yaml.FullLoader)

def __main():
    args = parse_args()
    config = load_config(args.config)
    containers_by_name = {}
    for container in config['containers']:
        containers_by_name[container['name']] = container
    if args.container not in containers_by_name:
        raise Exception('Container [%s] not found in config' % args.container)
    container = containers_by_name[args.container]
    podman_commands.run_container(container['image'], container['name'], container['run_args'])

__main()

