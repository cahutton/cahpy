"""TODO."""

from argparse import ArgumentParser


class ArgumentListError(Exception):
    """Exception raised on error with argument list."""

    pass


def parse_arguments(argument_list, description=None):
    """Parse args and opts."""
    parser = ArgumentParser(description=description)

    for argument in argument_list:
        try:
            name_or_flags = argument['name_or_flags']
        except KeyError:
            raise ArgumentListError('No name or flags provided.')

        metavar = argument.get('metavar', None)
        default = argument.get('default', None)
        help = argument.get('help', None)

        parser.add_argument(*name_or_flags, metavar=metavar, default=default,
                            help=help)

    return parser.parse_args()
