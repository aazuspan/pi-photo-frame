import threading
import os
import time


class MotionSensor:
    """A motion sensor that controls sleep state.
    
    On initialization, a thread is started that watches the motion sensor and
    sets the sleep state accordingly. When sleeping, the main `update` function
    will block until motion is detected.
    """
    def __init__(self, motion_gpio, sleep_after=1_200, motion_threshold=50_000):
        try:
            from gpiozero import MotionSensor
        except ImportError:
            raise ImportError("gpiozero is required for motion detection.")
        
        self.sensor = MotionSensor(motion_gpio, queue_len=30)
        self.sleep_after = sleep_after
        self.motion_threshold = motion_threshold

        self.is_checking = True
        self.is_awake = threading.Event()
        self.is_awake.set()
        self.check_thread = threading.Thread(target=self.check_loop)
        self.check_thread.start()

    def update(self):
        """Block execution if asleep."""
        self.is_awake.wait()

    def motion_detected(self):
        """Check the motion sensor for motion above a threshold."""
        motion_confirmed = False
        motion_count = 0
        while self.sensor.motion_detected and not motion_confirmed:
            motion_count += 1
            if motion_count > self.motion_threshold:
                motion_confirmed = True
        
        return motion_confirmed

    def check_loop(self):
        """Watch the motion sensor and set the sleep state."""
        last_motion = time.time()

        while self.is_checking:
            motion_confirmed = self.motion_detected()
                    
            if motion_confirmed:
                last_motion = time.time()
            time_to_sleep = time.time() - last_motion > self.sleep_after

            if not self.is_awake.is_set() and motion_confirmed:
                self.wake()
            elif self.is_awake.is_set() and time_to_sleep:
                self.sleep()
    
    def sleep(self):
        """Put the display to sleep and wait for motion."""
        self.is_awake.clear()
        os.system("vcgencmd display_power 0")

    def wake(self):
        """Wake the display from sleep."""
        self.is_awake.set()
        os.system("vcgencmd display_power 1")

    def stop(self):
        """Stop the motion sensor thread."""
        self.wake()
        self.is_checking = False
        self.check_thread.join()
