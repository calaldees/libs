# Pygame Helpers ---------------------------------------------------------------
#  Try to keep underlying implementation/libs of grapics handling away from logic

try:
    import pygame
except ImportError:
    pass

COLOR_BACKGROUND = (0, 0, 0, 255)


class SimplePygameBase(object):

    def __init__(self, width=320, height=240, framerate=3):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        self.running = True
        self.framerate = framerate

    def start(self):
        while self.running:
            self.clock.tick(self.framerate)
            self.screen.fill(COLOR_BACKGROUND)

            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    self.running = False

            self.loop()

            pygame.display.flip()

        pygame.quit()

    def stop(self):
        self.running = False

    def loop(self):
        assert False, 'loop must be overriden'
