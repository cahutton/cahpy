"""TODO."""


class Breakpoint(Exception):
    """TODO.

    Can be used as a one-line breakpoint:

        raise __import__('lib.debug', fromlist=['Breakpoint']).Breakpoint()
    """

    def __init__(self):
        """TODO."""
        super().__init__()

        self.with_traceback(None)

    def __str__(self):
        """TODO."""
        message = '\t>>> BREAKPOINT <<<\t'
        if self.args:
            if len(self.args) == 1:
                message += self.args[0]
            else:
                message += '(' + '; '.join(self.args) + ')'

        return message
