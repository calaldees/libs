import pygame
import pygame.midi


from pygame_midi_wrapper import PygameMidiDeviceHelper
from music import midi_status

import logging
log = logging.getLogger(__name__)


class MidiInput(object):

    def __init__(self, midi_input_name=None):
        self.midi_input_name = midi_input_name

    def open(self):
        pygame.init()
        pygame.display.set_caption(__name__)
        pygame.event.set_blocked(pygame.MOUSEMOTION)

        pygame.fastevent.init()
        self.event_get = pygame.fastevent.get
        self.event_post = pygame.fastevent.post

        pygame.midi.init()
        self.midi_input = PygameMidiDeviceHelper.open_device(self.midi_input_name, 'input')

        #pygame.display.set_mode((1, 1))
        self.run()

    def _process_events(self):
        events = self.event_get()
        for event in events:
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                self.running = False
            if event.type in [pygame.midi.MIDIIN]:
                self.midi_event(midi_status(event.status), event.data1, event.data2, event.data3)
        if self.midi_input.poll():
            for midi_event in pygame.midi.midis2events(self.midi_input.read(10), self.midi_input.device_id):
                self.event_post(midi_event)

    def run(self):
        try:
            self.running = True
            while self.running:
                self._process_events()
        except KeyboardInterrupt:
            pass
        self.close()

    def close(self):
        del self.midi_input
        pygame.midi.quit()

    def midi_event(self, status, data1, data2, data3):
        """
        To be overridden
        """
        log.debug((status, data1, data2, data3))
