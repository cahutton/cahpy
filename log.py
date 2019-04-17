"""TODO."""

from logging import captureWarnings, DEBUG, Formatter, getLogger, LogRecord, \
    StreamHandler


WARNINGS_LOGGER = getLogger('py.warnings')


class LinewiseStreamHandler(StreamHandler):
    """TODO."""

    def emit(self, record):
        """TODO."""
        for line in record.getMessage().split('\n'):
            line = line.strip()
            if line:
                super().emit(LogRecord(
                    record.name, record.levelno, record.pathname,
                    record.lineno, line, {}, record.exc_info))


class ObjectWithLogger(object):
    """TODO."""

    LOG_DIVIDER_WIDTH = 75
    LOG_FORMAT = '%(name)s  %(levelname).1s:  \t%(message)s'
    LOG_LEVEL = DEBUG
    LOGGER_NAME = 'LOG'

    def __init__(self):
        """TODO."""
        self.loggerHandler = LinewiseStreamHandler()
        self.loggerHandler.setFormatter(Formatter(self.LOG_FORMAT))
        self.loggerHandler.setLevel(self.LOG_LEVEL)

        WARNINGS_LOGGER.addHandler(self.loggerHandler)
        captureWarnings(True)

        self.logger = getLogger(self.LOGGER_NAME)
        self.logger.setLevel(self.LOG_LEVEL)
        self.logger.addHandler(self.loggerHandler)

        self.logDebug("Logging configured.")

        super().__init__()

    def __del__(self):
        """TODO."""
        self.logger.removeHandler(self.loggerHandler)

    @staticmethod
    def indentation(level=1):
        """TODO."""
        return '\t' * level

    def logMessage(self, level, message, indentation=0):
        """TODO."""
        output = self.indentation(indentation) + str(message)

        if level == 'critical':
            self.logger.critical(output)
        elif level == 'debug':
            self.logger.debug(output)
        elif level == 'error':
            self.logger.error(output)
        elif level == 'info':
            self.logger.info(output)
        elif level == 'warning':
            self.logger.warning(output)

    def logCritical(self, message, indentation=0):
        """TODO."""
        self.logMessage('critical', message, indentation)

    def logDebug(self, message, indentation=0):
        """TODO."""
        self.logMessage('debug', message, indentation)

    def logError(self, message, indentation=0):
        """TODO."""
        self.logMessage('error', message, indentation)

    def logHeader(self, logMethod, message='', symbol='=',
                  width=LOG_DIVIDER_WIDTH):
        """TODO."""
        horizontalRule = ''.join([symbol for column in range(width)])

        if message:
            logMethod(horizontalRule)
            logMethod(message)
        logMethod(horizontalRule)

    def logInfo(self, message, indentation=0):
        """TODO."""
        self.logMessage('info', message, indentation)

    def logWarning(self, message, indentation=0):
        """TODO."""
        self.logMessage('warning', message, indentation)
