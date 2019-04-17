"""TODO."""

from logging import getLogger
from re import match

import RPi.GPIO as GPIO
import RPIO


logger = getLogger()

DIGITS = {
    '''
 _ _ _
_     _
_     _

_     _
_     _
 _ _ _   _'''' ': '',
    '''
 _ _ _
_     _
_     _

_     _
_     _
 _ _ _   H''''.': 'H',
    '''
 A A A
F     B
F     B
 _ _ _
E     C
E     C
 D D D   _''''0': 'ABCDEF',
    '''
 _ _ _
_     B
_     B
 _ _ _
_     C
_     C
 _ _ _   _''''1': 'BC',
    '''
 A A A
_     B
_     B
 G G G
E     _
E     _
 D D D   _''''2': 'ABDEG',
    '''
 A A A
_     B
_     B
 G G G
_     C
_     C
 D D D   _''''3': 'ABCDG',
    '''
 _ _ _
F     B
F     B
 G G G
_     C
_     C
 _ _ _   _''''4': 'BCFG',
    '''
 A A A
F     _
F     _
 G G G
_     C
_     C
 D D D   _''''5': 'ACDFG',
    '''
 A A A
F     _
F     _
 G G G
E     C
E     C
 D D D   _''''6': 'ACDEFG',
    '''
 A A A
_     B
_     B

_     C
_     C
 _ _ _   _''''7': 'ABC',
    '''
 A A A
F     B
F     B
 G G G
E     C
E     C
 D D D   _''''8': 'ABCDEFG',
    '''
 A A A
F     B
F     B
 G G G
_     C
_     C
 _ _ _   _''''9': 'ABCFG'
}
DISPLAY_PATTERN = r'^[0-9 .]{1,4}$'
'''
PIN:     12      11       10        9        8       7
    _______________________________________________________
    |   A1            A2            A3            A4      |
    |F1    B1      F2    B2      F3    B3      F4    B4   |
    |   G1            G2            G3            G4      |
    |E1    C1      E2    C2      E3    C3      E4    C4   |
    |   D1    H1      D2    H2      D3    H3      D4    H4|
    |_____________________________________________________|

PIN:      1       2        3        4        5       6
'''
PINS = [None, 2, 3, 4, 17, 27, 22, 10, 9, 11, 25, 8, 7]
POSITIONS = {
    '1': PINS[12],
    '2': PINS[9],
    '3': PINS[8],
    '4': PINS[6]
}
SEGMENTS = {
    'A': PINS[11],
    'B': PINS[7],
    'C': PINS[4],
    'D': PINS[2],
    'E': PINS[1],
    'F': PINS[10],
    'G': PINS[5],
    'H': PINS[3]
}
SELECT_POSITION = True
SELECT_SEGMENT = False


def setDisplay(text):
    """TODO."""
    def getDigit(character, position=None):
        """TODO."""
        def getPosition(character):
            """TODO."""
            try:
                return POSITIONS[character]
            except KeyError:
                logger.error('Position ' + character + ' does not exist.')
                raise

        def getSegment(character):
            """TODO."""
            try:
                return SEGMENTS[character]
            except KeyError:
                logger.error('Segment ' + character + ' does not exist.')
                raise

        try:
            segments = DIGITS[character]
        except KeyError:
            logger.error('Digit ' + character + ' does not exist.')
            raise

        segments = [getSegment(segment) for segment in segments]

        if position is not None:
            segments.append(getPosition(position))

        return segments

    def setDigit(segments):
        """TODO."""
        for (pin, value) in segments.iteritems():
            RPIO.output(pin, value)

    if not match(DISPLAY_PATTERN, text):
        logger.warning('Bad input string.')

    digits = [
        getDigit(character, position)
        for character, position in enumerate(text)
    ]

    try:
        while(True):
            for digit in digits:
                setDigit(digit)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()


def configurePins():
    """TODO."""
    GPIO.setmode(GPIO.BOARD)

    for pin in PINS[1:]:
        RPIO.setup(pin, RPIO.OUT)
