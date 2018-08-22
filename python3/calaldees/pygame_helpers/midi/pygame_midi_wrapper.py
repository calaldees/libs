try:
    import pygame.midi
except ImportError:
    pass

from collections import namedtuple


import logging
log = logging.getLogger(__name__)


# Midi Device Helper -----------------------------------------------------------

class PygameMidiDeviceHelper(object):
    MidiDevice = namedtuple('MidiDevice', ('id', 'interf', 'name', 'input', 'output', 'opened'))

    @classmethod
    def get_device(self_class, id):
        return self_class.MidiDevice(*((id,)+pygame.midi.get_device_info(id)))

    @classmethod
    def get_devices(self_class):
        return (self_class.get_device(id) for id in range(pygame.midi.get_count()))

    @classmethod
    def open_device(self_class, name=None, io='output'):
        assert io in ('input', 'output'), 'Invalid io param'
        midi_device_id = -1
        if name:
            for midi_device in self_class.get_devices():
                if name.lower() in midi_device.name.decode('utf-8').lower() and bool(getattr(midi_device, io)):
                    midi_device_id = midi_device.id
        if midi_device_id < 0:
            log.warn("Unable to identify a midi device with name '{0}'".format(name))
            if io == 'input':
                midi_device_id = pygame.midi.get_default_input_id()
            if io == 'outout':
                midi_device_id = pygame.midi.get_default_output_id()
        if midi_device_id < 0:
            log.error('No {0} midi devices avalable'.format(io))
            return
        log.info("using midi {0} - {1}".format(io, self_class.get_device(midi_device_id)))
        if io == 'output':
            return pygame.midi.Output(midi_device_id)
        if io == 'input':
            return pygame.midi.Input(midi_device_id)

