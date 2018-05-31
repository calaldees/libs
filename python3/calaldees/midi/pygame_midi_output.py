import logging
log = logging.getLogger(__name__)


# Midi Wrapper -----------------------------------------------------------------

class PygameMidiOutputWrapperNull(object):
    def note(self, *args, **kwargs):
        pass

    def pitch(self, *args, **kwargs):
        pass


from .music import note_to_text, midi_pitch

class PygameMidiOutputWrapper(object):

    @staticmethod
    def factory(pygame_midi_output, channel=0):
        if pygame_midi_output:
            return PygameMidiOutputWrapper(pygame_midi_output, channel)
        return PygameMidiOutputWrapperNull()

    def __init__(self, pygame_midi_output, channel=0):
        assert pygame_midi_output, 'pygame_midi_output required'
        self.midi = pygame_midi_output
        self.channel = channel

    def note(self, note, velocity=0):
        """
        note int, velocity float 0->1
        """
        if not note:
            return
        velocity = int(velocity * 127)
        log.info('note: ch{0} - {1} {2} - {3}'.format(self.channel, note, note_to_text(note), velocity))
        self.midi.write_short(0x90 + self.channel, note, velocity)
        #if velocity:
        #    self.midi.note_on(note, velocity)
        #else:
        #    self.midi.note_off(note)
        #self.midi.write_short(0x90 + self.channel, note, 127)

    def pitch(self, pitch=0):
        """
        pitch float -1 to 1
        """
        log.info('pitch: ch{0} - {1}'.format(self.channel, pitch))
        self.midi.write_short(*midi_pitch(pitch, channel=self.channel))
