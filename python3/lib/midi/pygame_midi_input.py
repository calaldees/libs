import pygame
import pygame.midi


from .pygame_midi_wrapper import PygameMidiDeviceHelper
from .music import midi_status

import logging
log = logging.getLogger(__name__)


class MidiInput(object):
    MIDI_READ_SIZE = 64

    def __init__(self, midi_input_name=None):
        self.midi_input_name = midi_input_name

    def init_pygame(self):
        pygame.init()
        pygame.display.set_caption(__name__)
        pygame.event.set_blocked(pygame.MOUSEMOTION)

        pygame.fastevent.init()
        self.event_get = pygame.fastevent.get
        self.event_post = pygame.fastevent.post

        self.init_midi_input()
        #pygame.display.set_mode((1, 1))
        #self.run()
        self.running = False

    def init_midi_input(self):
        pygame.midi.init()
        self.midi_input = PygameMidiDeviceHelper.open_device(self.midi_input_name, 'input')

    def process_events(self, events=None):
        """
        Process a pygame eventlist
        if no eventlist is passed it will get the current eventlist
        This can be used when inside another game loop
        """
        if events == None:
            self._poll()
            events = self.event_get()
        for event in events:
            # Escape events (only used when inside the self.run() method
            if self.running and (event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE)):
                self.running = False
            # Midi events
            if event.type in [pygame.midi.MIDIIN]:
                self.midi_event(midi_status(event.status), event.data1, event.data2, event.data3)

    def run(self):
        """
        Run/Start a standalone loop to read from this input
        This is useful for test programs or simple standalone applications that don't require a game loop
        """
        try:
            self.running = True
            while self.running:
                self.process_events()
                if self.midi_input.poll():
                    self._poll()
        except KeyboardInterrupt:
            self.running = False
        self.close()

    def _poll(self):
        """
        Used inside an unrestricted loop to block for input
        """
        for midi_event in pygame.midi.midis2events(self.midi_input.read(self.MIDI_READ_SIZE), self.midi_input.device_id):
            self.event_post(midi_event)

    def close(self):
        del self.midi_input
        pygame.midi.quit()

    def midi_event(self, status, data1, data2, data3):
        """
        To be overridden
        """
        log.debug((status, data1, data2, data3))
