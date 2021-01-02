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
    parser = WrappedArgumentParser(description='Stops a podman container in the foreground')
    parser.add_argument("--container", type=str, metavar=('<container-name>'), required=True,
                        help='The name of the container defined in the config file to run')
    return parser.parse_args()

def __main():
    args = parse_args()
    podman_commands.stop_container_if_exists(args.container)

__main()

