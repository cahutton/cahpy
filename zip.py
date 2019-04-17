"""Tools for working with .ZIP files."""

from pathlib import Path
from zipfile import BadZipFile, is_zipfile, ZipFile

from cahpy.filesystem import get_CRC, get_file_size
from cahpy.log import ObjectWithLogger
from cahpy.system import ExitException


def decompress_all(path):
    """Unzip all .ZIP files under a path."""
    Zip.decompressFiles(Zip.getAll(path))


class Zip(ObjectWithLogger):
    """An object for .ZIP files."""

    FILE_EXTENSION = '.zip'
    LOGGER_NAME = 'Zip'

    def __init__(self, filePath):
        """Initialize a Zip instance."""
        super().__init__()

        if not isinstance(filePath, str):
            filePath = str(filePath)

        if not is_zipfile(filePath):
            self.logError('...not a zipfile.')

            raise ExitException

        try:
            # with ZipFile(filePath) as file:
            #     ...
            self.zipFile = ZipFile(filePath)
            if self.zipFile.testzip():
                raise BadZipFile
        except BadZipFile:
            self.logError('...bad zipfile.')

            raise ExitException

    @classmethod
    def decompressFile(cls, path):
        """Unzip a single file."""
        pathString = str(path)

        file = cls(pathString)
        file.logInfo('Decompressing ' + pathString + '...')
        file.extractAllFiles(path.parent)
        file.logInfo('...' + pathString + ' decompressed.')

    @classmethod
    def decompressFiles(cls, paths):
        """Unzip all files in a list of paths."""
        for path in paths:
            cls.decompressFile(path)

    def extractAllFiles(self, targetPath):
        """TODO."""
        for file in self.zipFile.infolist():
            self.extractFile(file, targetPath)

    def extractFile(self, file, targetPath):
        """TODO."""
        self.logInfo('Extracting ' + file.filename + '...')
        existingFilePath = targetPath / file.filename

        if file.file_size == get_file_size(existingFilePath) \
                and file.CRC == get_CRC(existingFilePath):
            self.logInfo('...file with same size and checksum already exists.')

            return

        self.zipFile.extract(file, str(targetPath))
        self.logInfo('...' + file.filename + ' extracted.')

    @classmethod
    def getAll(cls, path, globPattern='**/*' + FILE_EXTENSION,
               returnSorted=True):
        """Get a list of paths of all .ZIP files under a path."""
        if not isinstance(path, Path):
            path = Path(path)

        files = path.glob(globPattern)

        return sorted(files) if returnSorted else files
