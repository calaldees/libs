from collections import namedtuple


# Midi Utils -------------------------------------------------------------------

def midi_pitch(pitch_bend_value, channel=0):
    """
    pitch bend is a float from -1 to 1 (0 is no change)
    A special midi command needs to be sent (0xEn) with a 14-bit encoded range (+/- 8192)

    http://forum.arduino.cc/index.php?topic=119790.0
    http://www.tonalsoft.com/pub/pitch-bend/pitch.2005-08-24.17-00.aspx

    ##>>> midi_pitch(-0.1241455078125)  # 1016 (0xE0, 0x70, 0x37)

    >>> midi_pitch(0)  # (0xE0, 0x00, 0x40)
    (224, 0, 64)
    >>> midi_pitch(0, channel=1)  # (0xE1, 0x00, 0x40)
    (225, 0, 64)
    >>> midi_pitch(1)  # (0xE0, 0x7F, 0x7F)
    (224, 127, 127)
    >>> midi_pitch(-1)  # (0xE0, 0x01, 0x00)
    (224, 1, 0)
    """
    change = 0x2000 + int(pitch_bend_value * 0x1FFF);
    return (0xE0 + channel, change & 0x7F, (change >> 7) & 0x7F)


MidiStatus = namedtuple('MidiStatus', ['code', 'name', 'channel'])
MIDI_STATUS_LOOKUP = {
    0x8: 'note_off',
    0x9: 'note_on',
    0xA: 'polyphonic_aftertouch',
    0xB: 'control_change',
    0xC: 'program_change',
    0xD: 'channel_aftertouch',
    0xE: 'pitch_wheel',
}
def midi_status(status_byte):
    """
    >>> midi_status(144)
    MidiStatus(code=9, name='note_on', channel=0)
    """
    status_code = status_byte//16
    return MidiStatus(
        code=status_code,
        name=MIDI_STATUS_LOOKUP[status_code],
        channel=status_byte % 16,
    )
