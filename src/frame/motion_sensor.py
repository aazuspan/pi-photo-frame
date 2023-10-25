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

        self.is_asleep = threading.Event()
        threading.Thread(target=self.check_loop).start()

    def update(self):
        """Block execution if asleep."""
        self.is_asleep.wait()

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

        while True:
            motion_confirmed = self.motion_detected()
                    
            if motion_confirmed:
                last_motion = time.time()
            time_to_sleep = time.time() - last_motion > self.sleep_after

            if self.is_asleep.is_set() and motion_confirmed:
                self.wake()
            elif not self.is_asleep.is_set() and time_to_sleep:
                self.sleep()
    
    def sleep(self):
        """Put the display to sleep and wait for motion."""
        self.is_asleep.set()
        hdmi_off()

    def wake(self):
        """Wake the display from sleep."""
        self.is_asleep.clear()
        hdmi_on()


def hdmi_off():
    os.system("vcgencmd display_power 0")


def hdmi_on():
    os.system("vcgencmd display_power 1")