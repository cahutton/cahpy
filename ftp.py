"""Tools for downloading files using FTP."""

from contextlib import contextmanager
from ftplib import error_perm, error_temp, FTP, FTP_PORT
from socket import gaierror, timeout
from time import sleep

from cahpy.filesystem import get_file_size, make_directory_if_not_exists
from cahpy.internet import can_connect_to_internet
from cahpy.log import ObjectWithLogger
from cahpy.system import ExitException


class FtpClient(ObjectWithLogger):
    """An FTP client."""

    ANONYMOUS_USER = 'anonymous'
    ATTEMPTS = 10
    LOGGER_NAME = 'FTP'
    SLEEP_TIME = 1  # s
    TIMEOUT = 3  # s

    def __init__(self):
        """Initialize an FtpClient instance."""
        super().__init__()

        class _FTP(FTP):
            FTP_CLIENT = self

            def connect(self, *args, **kwargs):
                result = super().connect(*args, **kwargs)

                self.FTP_CLIENT.logDebug(result)

                return result

            def cwd(self, *args, **kwargs):
                result = super().cwd(*args, **kwargs)

                self.FTP_CLIENT.logInfo(result)

                return result

            def login(self, *args, **kwargs):
                result = super().login(*args, **kwargs)

                self.FTP_CLIENT.logDebug(result)

                return result

            def retrbinary(self, *args, **kwargs):
                result = super().retrbinary(*args, **kwargs)

                self.FTP_CLIENT.logDebug(result)

                return result

        self._FTP = _FTP

    @contextmanager
    def connect(self, server, username=ANONYMOUS_USER, attempts=ATTEMPTS):
        """Connect to an FTP server."""
        connected = False

        if not can_connect_to_internet():
            self.logError('No Internet connection.')

            raise ExitException()

        while attempts:
            try:
                with self._FTP() as connection:
                    self.connection = connection

                    self.logInfo('Connecting to ' + server + '...')
                    connection.connect(server, FTP_PORT, self.TIMEOUT)
                    connected = True
                    self.logInfo(
                        '...connected; logging in as ' + username + '...')
                    connection.login(username)
                    self.logInfo(
                        '...logged in; yielding connection...')

                    yield connection

                    connection.quit()
            except ConnectionResetError:
                self.logDebug('...connection reset...')
                # TODO: save operation state, get new connection, retry
            except error_perm as error:
                self.logError(
                    '...permanent FTP error: "' + error.args[0] + '"...')
                attempts = 1
            except error_temp as error:
                self.logError(
                    '...temporary FTP error: "' + error.args[0] + '"...')
            except gaierror as error:
                self.logDebug(
                    '...error getting address info; error code '
                    + str(error.errno) + ': "' + error.strerror + '"...')
                if error.errno == -2:  # Name or service not known
                    self.logDebug('server = ' + str(server) +
                                  '\nusername = ' + str(username))
                attempts = 1
            except timeout:
                self.logDebug('...socket timed out...')
            except TimeoutError:
                self.logDebug('...connection timed out...')
            else:
                return

            attempts -= 1
            if attempts:
                self.logDebug(
                    '...retrying (' + str(attempts) + ' more attempts)...')
                sleep(self.SLEEP_TIME)

        if connected:
            self.logError('...connection aborted.')
        else:
            self.logError('...couldn\'t connect.')

        raise ExitException()

    def download(self, downloads, baseDownloadPath):
        """TODO."""
        make_directory_if_not_exists(baseDownloadPath)

        for server, items in downloads.items():
            with self.connect(server):
                for item in items:
                    try:
                        self.connection.cwd(item['path'])
                    except error_perm as error:
                        if error.args[0] != '550 Failed to change directory.':
                            raise

                        isDirectory = False
                    else:
                        isDirectory = True

                    (self.downloadDirectory if isDirectory
                     else self.downloadFile)(item['path'],
                                             baseDownloadPath / item['saveAs'])

    def downloadDirectory(self, sourcePath, targetPath, attempts=ATTEMPTS):
        """TODO."""
        self.logDebug('Downloading directory ' + sourcePath + ' to '
                      + str(targetPath) + '...')
        make_directory_if_not_exists(targetPath)

        for fileName in sorted(self.connection.nlst()):
            self.downloadFile(fileName, targetPath / fileName, attempts)

        self.logDebug('...directory ' + sourcePath + ' downloaded.')

    def downloadFile(self, fileName, downloadPath, attempts=ATTEMPTS):
        """TODO."""
        while attempts:
            self.logInfo('Downloading ' + fileName + '...')
            if self.connection.size(fileName) == get_file_size(downloadPath):
                self.logInfo('...file already exists; skipping.')

                return
            with downloadPath.open('w+b') as destinationFile:
                try:
                    self.connection.retrbinary('RETR ' + fileName,
                                               destinationFile.write,
                                               rest=destinationFile.tell())
                except error_perm as error:
                    self.logError(error.args[0])
                    self.logError('...FTP error; skipping.')

                    return
                except error_temp as error:
                    self.logError(error.args[0])
                    self.logError('...FTP error...')
                else:
                    self.logInfo('...' + fileName + ' downloaded.')

                    return

            attempts -= 1
            if attempts:
                self.logDebug(
                    '...retrying (' + str(attempts) + ' more attempts)...')
                sleep(self.SLEEP_TIME)

        self.logWarning('...couldn\'t download ' + fileName + '.')
