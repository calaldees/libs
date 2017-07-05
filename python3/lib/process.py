import multiprocessing


class SingleOutputStopableProcess():
    def __init__(self, func):
        self.queue = multiprocessing.Queue(1)
        self.func = func
        self.close_event = None
        self.process = None

    def stop(self):
        if self.close_event:
            self.close_event.set()
            self.process.join()
            self.close_event = None
            self.process = None

    def start(self, *args, **kwargs):
        """
        `func` is a function that's first two arguments are queue and close
        """
        self.stop()
        self.close_event = multiprocessing.Event()
        self.process = multiprocessing.Process(
            target=self.func,
            args=(
                self.queue,
                self.close_event,
                *args,
            ),
            kwargs=kwargs
        )
        self.process.start()

    def onComplete(self):
        raise NotImplementedError()
