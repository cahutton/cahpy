"""TODO."""

from contextlib import contextmanager
from http.client import HTTP_PORT, HTTPConnection, HTTPException, \
    HTTPS_PORT, HTTPSConnection
from http.cookiejar import CookieJar
from socket import gaierror
from time import sleep
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request

from cahpy.filesystem import get_file_size, get_last_modified_time, \
    make_directory_if_not_exists
from cahpy.internet import can_connect_to_internet
from cahpy.log import ObjectWithLogger
from cahpy.system import ExitException


DELETE = 'DELETE'
GET = 'GET'
HEAD = 'HEAD'
OPTIONS = 'OPTIONS'
PATCH = 'PATCH'
POST = 'POST'
PUT = 'PUT'
SAFE_HTTP_METHODS = NULLIPOTENT_HTTP_METHODS = [GET, HEAD, OPTIONS]
UNSAFE_IDEMPOTENT_HTTP_METHODS = [DELETE, PUT]
NON_IDEMPOTENT_HTTP_METHODS = [PATCH, POST]
IDEMPOTENT_HTTP_METHODS = sorted(SAFE_HTTP_METHODS
                                 + UNSAFE_IDEMPOTENT_HTTP_METHODS)
UNSAFE_HTTP_METHODS = sorted(UNSAFE_IDEMPOTENT_HTTP_METHODS
                             + NON_IDEMPOTENT_HTTP_METHODS)
HTTP_METHODS = sorted(SAFE_HTTP_METHODS + UNSAFE_IDEMPOTENT_HTTP_METHODS
                      + NON_IDEMPOTENT_HTTP_METHODS)

REDIRECT_STATUS_CODES = (301, 302, 303, 307, 308)
SERVER_ROOT = '/'
SERVER_WIDE_REQUEST_TARGET = '*'


def format_http_header(header, argument):
    """Format an HTTP header."""
    return header + ': ' + argument


class HttpClient(ObjectWithLogger):
    """An HTTP client."""

    ATTEMPTS = 10
    LOGGER_NAME = 'HTTP'
    SLEEP_TIME = 1  # s
    TIMEOUT = 3  # s

    DEFAULT_ACCEPT_HEADERS = {
        'Accept': '*/*;q=0.1',
        'Accept-Charset': 'utf-8;q=1.0, *;q=0.1',
        'Accept-Encoding': 'gzip, br, deflate;q=1.0, *;q=0.5',
        'Accept-Language': 'en-US, en;q=1.0, *;q=0.5'
    }
    DEFAULT_ACCESS_CONTROL_REQUEST_HEADERS = {
        'Access-Control-Request-Headers':
            'Accept, Accept-Charset, Accept-Encoding, Accept-Language,'
            ' Connection, Content-Type, DNT',
        'Access-Control-Request-Method': 'GET, HEAD, OPTIONS'
    }
    DEFAULT_HEADERS = {
        'Connection': 'keep-alive',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1'
    }
    DEFAULT_HEAD_HEADERS = dict(**DEFAULT_HEADERS, **DEFAULT_ACCEPT_HEADERS)
    DEFAULT_OPTIONS_HEADERS = dict(**DEFAULT_HEADERS,
                                   **DEFAULT_ACCESS_CONTROL_REQUEST_HEADERS)

    isHeadAllowed = None
    isOptionsAllowed = None

    def __init__(self):
        """Initialize an HttpClient instance."""
        super().__init__()

        self.cookieJar = CookieJar()

    @contextmanager
    def connect(self, server, protocol='https', attempts=ATTEMPTS):
        """Connect to an HTTP server."""
        if not can_connect_to_internet():
            self.logError('No Internet connection.')

            raise ExitException()

        self.url = urlsplit(urlunsplit((protocol, server, '', '', '')))

        if self.url.scheme == 'https':
            connectionClass = HTTPSConnection
            port = HTTPS_PORT
        elif self.url.scheme == 'http':
            connectionClass = HTTPConnection
            port = HTTP_PORT
        else:
            self.logError('Unknown protocol.')

            raise ExitException()

        while attempts:
            try:
                self.connection = connectionClass(self.url.netloc, port=port,
                                                  timeout=self.TIMEOUT)

                self.logInfo('Connecting to ' + self.url.netloc + '...')
                self.connection.connect()
                self.logInfo('...connected; checking server options...')
                self.requestServerOptions()
                self.logInfo('...connection negotiated; yielding...')

                yield self.connection
            except gaierror as error:
                self.logDebug(
                    '...error getting address info; error code '
                    + str(error.errno) + ': "' + error.strerror + '"...')
                if error.errno == -2:  # Name or service not known
                    self.logDebug('netloc = ' + str(self.url.netloc))
                attempts = 1
            except HTTPException:
                raise
            except HttpRedirect as redirect:
                self.logInfo('...following redirect...')
                with self.connect(redirect.url.netloc, attempts=attempts) \
                        as connection:
                    yield connection
            else:
                return
            finally:
                self.logInfo('...closing connection...')
                self.connection.close()

            attempts -= 1
            if attempts:
                self.logDebug(
                    '...retrying (' + str(attempts) + ' more attempts)...')
                sleep(self.SLEEP_TIME)

        self.logError('...couldn\'t connect.')

        raise ExitException()

    def download(self, downloads, baseDownloadPath):
        """TODO."""
        make_directory_if_not_exists(baseDownloadPath)

        for server, files in downloads.items():
            with self.connect(server):
                for file in files:
                    self.downloadFile(file['url'],
                                      baseDownloadPath / file['saveAs'])

    def downloadFile(self, source, destination, attempts=ATTEMPTS,
                     force=False):
        """TODO."""
        self.logInfo('Downloading ' + source + '...')

        if isinstance(source, str):
            self.url = urlsplit(source)
        self.logDebug(self.url)

        doHead = self.isHeadAllowed
        doOptions = self.isOptionsAllowed
        headers = dict(**self.DEFAULT_HEADERS,
                       **self.DEFAULT_ACCEPT_HEADERS)
        resource = urlunsplit(('', '', self.url.path, self.url.query, ''))

        if not force:
            last_modified = get_last_modified_time(destination)
            if last_modified:
                headers['If-Modified-Since'] = last_modified
            # TODO: use ETag
            # etag = etag(destination)
            # if etag:
            #     headers['If-None-Match'] = etag

        while attempts:
            if doOptions:
                with self.requestOptions(resource,
                                         headers=headers) as response:
                    pass

            if doHead:
                with self.requestHead(resource, headers=headers) as response:
                    # TODO: if 'Last-Modified' >
                    if not force and response.status == 304:
                        self.logInfo('...remote file not modified; skipping.')

                        return

                    if response.getheader('Content-Length') \
                            == get_file_size(destination):
                        self.logInfo('...file already exists; skipping.')

                        return

            try:
                with self.request(resource, headers=headers) as response:
                    if response.status in REDIRECT_STATUS_CODES:
                        raise HttpRedirect(response.status,
                                           response.getheader('Location'))
                    elif not force and response.status == 304:
                        self.logInfo('...remote file not modified; skipping.')

                        return
                    elif response.status == 200:
                        self.logInfo(
                            '...saving as ' + str(destination) + '...')
                        with destination.open('w+b') as destinationFile:
                            destinationFile.write(response.read())
                            # for chunk in response.iter_content(ONE_MEGABYTE):
                            #     if chunk:
                            #         destinationFile.write(chunk)
                            #         destinationFile.flush()

                        # TODO: store ETag
                        # if response.getheader('ETag'):
                        #     save_etag(response.headers['ETag'])
            except HTTPException as error:
                self.logError(error.args[0])
                self.logError('...HTTP error...')
            except HttpRedirect as redirect:
                if redirect.url.scheme != self.url.scheme \
                        or redirect.url.netloc != self.url.netloc:
                    raise redirect

                self.url = redirect.url
                resource = \
                    urlunsplit(('', '', self.url.path, self.url.query, ''))
                doHead = False

                continue
            else:
                self.logInfo('...' + source + ' downloaded.')

                return

            attempts -= 1
            if attempts:
                self.logDebug(
                    '...retrying (' + str(attempts) + ' more attempts)...')
                sleep(self.SLEEP_TIME)

        self.logWarning('...couldn\'t download ' + source + '.')

    @staticmethod
    def formatHeader(header, argument):
        """Format an HTTP header."""
        return format_http_header(header, argument)

    @contextmanager
    def request(self, resource, method=GET, headers=None, messageBody=None):
        """TODO."""
        if headers is None:
            headers = {}
            skipAcceptEncoding = skipHost = False
        else:
            skipAcceptEncoding = 'Accept-Encoding' in headers
            skipHost = 'Host' in headers
        request = Request(urlunsplit(self.url), headers=headers, method=method)
        self.cookieJar.add_cookie_header(request)
        headers = sorted(request.header_items())

        self.logInfo('...starting request...')
        self.logDebug(method + ' ' + resource + ' HTTP/1.1')
        self.connection.putrequest(method, resource, skip_host=skipHost,
                                   skip_accept_encoding=skipAcceptEncoding)

        if headers:
            self.logDebug('...sending headers...')
            for header, argument in headers:
                self.logDebug(self.formatHeader(header, argument))
                self.connection.putheader(header, argument)

        if messageBody:
            self.logDebug('...sending message body...')
            # self.logDebug(messageBody)
            self.connection.endheaders(messageBody)
        else:
            self.connection.endheaders()

        self.logDebug('...getting response...')
        with self.connection.getresponse() as response:
            self.logInfo('...response received...')
            self.logDebug(str(response.status) + ' ' + response.reason)
            for header, argument in response.getheaders():
                self.logDebug(self.formatHeader(header, argument))
            # self.logDebug(response.read())

            self.cookieJar.extract_cookies(response, request)

            yield response

    def requestHead(self, resource, headers=None):
        """TODO."""
        if headers is None:
            headers = self.DEFAULT_HEAD_HEADERS

        return self.request(resource, HEAD, headers=headers)

    def requestOptions(self, resource, headers=None):
        """TODO."""
        if headers is None:
            headers = self.DEFAULT_OPTIONS_HEADERS

        return self.request(resource, OPTIONS, headers=headers)

    def requestServerOptions(self, headers=None):
        """TODO."""
        if headers is None:
            headers = self.DEFAULT_HEADERS

        with self.request(SERVER_WIDE_REQUEST_TARGET, OPTIONS,
                          headers=headers) as response:
            if response.status == 200:
                if HEAD in response.getheader('Allow'):
                    self.isHeadAllowed = True
            elif response.status in REDIRECT_STATUS_CODES:
                location = response.getheader('Location')
                if location.split('://')[1] \
                        == self.server + SERVER_WIDE_REQUEST_TARGET:
                    location = location[:-1]

                raise HttpRedirect(response.status, location)
            elif response.status >= 400:
                with self.requestOptions(SERVER_ROOT) as rootOptionsResponse:
                    if rootOptionsResponse.status == 200:
                        self.isOptionsAllowed = True
                    elif rootOptionsResponse.status >= 400:
                        self.isOptionsAllowed = False

                if not self.isOptionsAllowed:
                    with self.requestHead(SERVER_ROOT) as rootHeadResponse:
                        if rootHeadResponse.status == 200:
                            self.isHeadAllowed = True
                        elif rootHeadResponse.status >= 404:
                            self.isHeadAllowed = False


class HttpRedirect(Exception):
    """TODO."""

    def __init__(self, status_code, location):
        """TODO."""
        super().__init__()

        self.status_code = status_code
        self.url = urlsplit(location)
