import multiprocessing


class SingleOutputStopableProcess():
    def __init__(self, func, queue_size=1):
        self.queue = multiprocessing.Queue(queue_size)
        self.func = func
        self.close_event = None
        self.process = None

    def stop(self):
        if self.close_event:
            self.close_event.set()
            self.close_event = None
        if self.process:
            self.process.join()
            self.process = None

    def start(self, *args, **kwargs):
        """
        `func` is a function that's first two arguments are queue and close
        """
        self.stop()
        self.close_event = multiprocessing.Event()
        self.process = multiprocessing.Process(
            name=self.func.__name__,
            target=self.func,
            args=(
                self.queue,
                self.close_event,
                *args,
            ),
            kwargs=kwargs
        )
        self.process.start()

    def is_running(self):
        return self.close_event and not self.close_event.is_set()

    def onComplete(self):
        raise NotImplementedError()
