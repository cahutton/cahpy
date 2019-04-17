"""TODO."""

from binascii import crc32
from errno import EEXIST
from os import makedirs, mkdir
from os.path import exists, getmtime, getsize, isdir, isfile
from pathlib import Path
from time import gmtime, strftime


RFC_7231_TIMESTAMP_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'


class DirectoryExistsError(FileExistsError):
    """TODO."""

    def __init__(self, directory_name):
        """TODO."""
        self.directory_name = directory_name

        super().__init__(
            '...a directory named ' + directory_name + ' already exists...')


def get_CRC(filePath):
    """TODO."""
    if not isinstance(filePath, str):
        filePath = str(filePath)

    with open(filePath, 'rb') as file:
        return crc32(file.read()) & 0xFFFFFFFF


def get_file_size(filePath):
    """TODO."""
    if not isinstance(filePath, str):
        filePath = str(filePath)

    try:
        return getsize(filePath)
    except FileNotFoundError:
        return None


def get_formatted_time(seconds):
    """TODO."""
    return strftime(RFC_7231_TIMESTAMP_FORMAT, gmtime(seconds))


def get_last_modified_time(filePath):
    """TODO."""
    if not isinstance(filePath, str):
        filePath = str(filePath)

    return get_formatted_time(getmtime(filePath) if isfile(filePath) else 0)


def make_directory_if_not_exists(directoryPath):
    """TODO."""
    if isinstance(directoryPath, str):
        directoryPathString = directoryPath
        directoryPath = Path(directoryPath)
    else:
        directoryPathString = str(directoryPath)

    try:
        makedirs(directoryPathString)
    except OSError as error:
        if error.errno != EEXIST:
            raise

    return directoryPath


def prepare_directories(directories):
    """TODO."""
    for directory in directories:
        if not exists(directory):
            mkdir(directory)
        elif not isdir(directory):
            raise DirectoryExistsError(directory)
    # except DirectoryExistsError as error:
    #     logger.critical(error.message)
    #     logger.critical('...could not create directory ' + error.file_name
    #                     + '; exiting.')
    #     raise
