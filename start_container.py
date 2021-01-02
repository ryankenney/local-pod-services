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

def __main():
    args = parse_args()
    config = load_config(args.config)
    podman_commands.run_container(config['image'], config['name'], config['run_args'])

__main()

