"""TODO."""

from subprocess import PIPE, Popen, STDOUT, TimeoutExpired

from cahpy.log import ObjectWithLogger


class ExitException(Exception):
    """TODO."""

    def __init__(self, returnCode=1):
        """TODO."""
        super().__init__()

        self.returnCode = returnCode


class Subprocess(ObjectWithLogger):
    """TODO."""

    TIMEOUT = 15  # s

    def do(self, args, stdin=None, stdout=PIPE, stderr=STDOUT, cwd=None):
        """TODO."""
        with Popen(args, stdin=stdin, stdout=stdout, stderr=stderr, cwd=cwd,
                   universal_newlines=True) as process:
            try:
                stdout_data, stderr_data = \
                    process.communicate(timeout=self.TIMEOUT)
            except TimeoutExpired:
                process.kill()
                stdout_data, stderr_data = process.communicate()
            finally:
                if stdout_data:
                    self.logInfo(stdout_data)
                if stderr_data:
                    self.logError(stderr_data)

                return process.returncode
