import time


class Loop(object):
    SLEEP_FACTOR = 0.8

    class LoopInterruptException(Exception):
        pass

    def __init__(self, fps, timeshift=0):
        self.set_period(fps)
        self.profile_timelog = []
        self.timeshift = timeshift

    def set_period(self, fps):
        assert fps, "Provide fps"
        self.fps = fps
        self.period = 1 / fps
        self.start_time = time.time()
        self.previous_time = self.start_time
        return self.period

    def get_frame(self, timestamp):
        return int((timestamp - self.start_time + self.timeshift) // self.period)

    def is_running(self):
        return self.running

    def run(self):
        self.running = True
        try:
            while self.is_running() and self.period:
                self.current_time = time.time()

                current_frame = self.get_frame(self.current_time)
                previous_frame = self.get_frame(self.previous_time)
                for frame in range(previous_frame, current_frame):
                    self.render(frame)

                self.previous_time = self.current_time

                sleep_time = (self.start_time + (self.period * (current_frame + 1)) - time.time()) * self.SLEEP_FACTOR
                if sleep_time > 0:
                    time.sleep(sleep_time)
        except KeyboardInterrupt:
            pass
        except self.LoopInterruptException:
            pass
        self.close()

    def close(self):
        pass

    def render(self, frame):
        """
        This method is to be overridden under normal operation.
        The implementation here is useful for measuring the accuracy of the rendered frames.
        self.profile_timelog contains the time the redered frame was out from it's expected time.
        This is useful to run and average
        """
        #print('{0} {1}'.format(frame, time.time()))
        self.profile_timelog.append(self.current_time - (self.start_time + (self.period * frame)))
        if frame > (self.fps*20):
            average_frame_inacuracy = sum(self.profile_timelog)/len(self.profile_timelog)
            average_off_percent = average_frame_inacuracy / self.period
            variance = max(self.profile_timelog) - min(self.profile_timelog)
            print('average_frame_inacuracy: {0} average_off_percent: {1:.2%} variance: {2}'.format(average_frame_inacuracy, average_off_percent, variance))
            self.running = False


if __name__ == "__main__":
    Loop(60).loop()
