import multiprocessing


def multiprocessing_process_event_queue(queue_event_processors, is_running=True):
    """
    Process multiple 'ready' multiprocess.Queue's on a single thread.
    Dispatch each queue to a handler function
    Example of use:

        multiprocessing_process_event_queue({
            self.network_event_queue: self.network_event,
            self.scan_update_event_queue: self.scan_update_event,
        })
    """
    for queue, func in queue_event_processors.items():
        assert hasattr(queue, '_reader')
        assert hasattr(func, '__call__')
    _is_running = is_running if hasattr(is_running, '__call__') else lambda: is_running
    def wait_for_queue_to_be_ready(queues):
        _queue_lookup = {getattr(queue, '_reader'): queue for queue in queues}
        while _is_running():
            try:
                for queue in (
                        _queue_lookup[reader]
                        for reader in multiprocessing.connection.wait(
                            _queue_lookup.keys(),
                            timeout=1.0,
                        )
                ):
                    yield queue
            except KeyboardInterrupt:
                break
    for ready_queue in wait_for_queue_to_be_ready(queue_event_processors.keys()):
        queue_event_processors[ready_queue](ready_queue.get())

