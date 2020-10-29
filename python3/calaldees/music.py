""" Music Note Utils """

import re
from types import MappingProxyType

# Human readable input/output --------------------------------------------------

LOOKUP_NOTE_STR = {
    0: 'C',
    1: 'C#',
    2: 'D',
    3: 'D#',
    4: 'E',
    5: 'F',
    6: 'F#',
    7: 'G',
    8: 'G#',
    9: 'A',
    10: 'A#',
    11: 'B',
}
LOOKUP_STR_NOTE = {text: note for note, text in LOOKUP_NOTE_STR.items()}
NUM_NOTES_IN_OCTAVE = len(LOOKUP_NOTE_STR)
OFFSET_FROM_C0 = NUM_NOTES_IN_OCTAVE * 2


def note_to_text(note):
    """
    >>> note_to_text(0)
    'C-2'
    >>> note_to_text(24)
    'C0'
    >>> note_to_text(60)
    'C3'
    >>> note_to_text(61)
    'C#3'
    """
    return '{0}{1}'.format(
        LOOKUP_NOTE_STR[note % NUM_NOTES_IN_OCTAVE],
        (note-OFFSET_FROM_C0)//NUM_NOTES_IN_OCTAVE
    )


def parse_note(item):
    """
    >>> parse_note('C-2')
    0
    >>> parse_note('C0')
    24
    >>> parse_note('C3')
    60
    >>> parse_note('C#3')
    61
    >>> parse_note('60')
    60
    >>> parse_note(60)
    60
    """
    try:
        item = int(item)
        if item >= 0:  # todo, upper limit?
            return item
    except:
        pass
    try:
        note_str, octave = re.match(r'([ABCDEFG]#?)(-?\d{1,2})', item.upper()).groups()
        return LOOKUP_STR_NOTE[note_str] + (int(octave) * NUM_NOTES_IN_OCTAVE) + OFFSET_FROM_C0
    except Exception:
        raise Exception('Unable to parse note {0}'.format(item))


# Scale definitions ------------------------------------------------------------

class Scale(object):
    def __init__(self, scale):
        self.scale = scale

    @property
    def len(self):
        return len(self.scale)

    def scale_note(self, scale_index):
        """
        Calculate the distance in semitones from the scale's root

        >>> s = Scale((0, 2, 4, 7, 9))
        >>> s.scale_note(0)
        0
        >>> s.scale_note(1)
        2
        >>> s.scale_note(2)
        4
        >>> s.scale_note(5)
        12
        >>> s.scale_note(9)
        21
        """
        index = scale_index % self.len
        octave = scale_index // self.len
        return self.scale[index] + (octave * NUM_NOTES_IN_OCTAVE)


SCALES = MappingProxyType({
    # Full scales
    'ionian': Scale((0, 2, 4, 5, 7, 9, 11)),  # major scale
    'dorian': Scale((0, 2, 3, 5, 7, 9, 10)),
    'phrygian': Scale((0, 1, 3, 5, 7, 8, 10)),
    'lydian': Scale((0, 2, 4, 6, 7, 9, 11)),
    'mixolidian': Scale((0, 2, 4, 5, 7, 9, 10)),
    'aeolian': Scale((0, 2, 3, 5, 7, 8, 10)),  # relative minor
    'locrian': Scale((0, 1, 3, 5, 6, 8, 10)),

    # 5 note scales
    'pentatonic_major': Scale((0, 2, 4, 7, 9)),
    'pentatonic_minor': Scale((0, 3, 5, 7, 10)),
    'pentatonic_blues': Scale((0, 3, 5, 6, 7, 10)),
    'pentatonic_neutral': Scale((0, 2, 5, 7, 10)),

    'diatonic': Scale((0, 2, 4, 7, 9)),  # same as pentatonic major

    'balinese': Scale((0, 1, 3, 7, 8)),
    'chinese': Scale((0, 4, 6, 7, 11)),
    'egyptian': Scale((0, 2, 5, 7, 10)),
    'hirajoshi': Scale((0, 2, 3, 7, 8)),
    'japanise_a': Scale((0, 1, 5, 7, 8)),
    'japanise_b': Scale((0, 2, 5, 7, 8)),
    'kumoi': Scale((0, 2, 3, 7, 9)),
    'pelong': Scale((0, 1, 3, 7, 8)),
})
