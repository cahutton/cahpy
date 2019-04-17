"""TODO."""

from os.path import join

from configparser import ConfigParser, ExtendedInterpolation


DEFAULT_CONFIG_PATH = join('config', 'default.cfg')


def get_configuration(file_name=DEFAULT_CONFIG_PATH):
    """TODO."""
    configuration = ConfigParser(interpolation=ExtendedInterpolation())
    configuration.read(file_name)

    return configuration
