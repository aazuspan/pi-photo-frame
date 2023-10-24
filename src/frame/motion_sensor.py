import os
import time


class MotionSensor:
    def __init__(self, motion_gpio, sleep_after=1_200, motion_threshold=50_000):
        try:
            from gpiozero import MotionSensor
        except ImportError:
            raise ImportError("gpiozero is required for motion detection.")
        
        self.is_awake = True
        self.sensor = MotionSensor(motion_gpio, queue_len=30)
        self.sleep_after = sleep_after
        self.motion_threshold = motion_threshold
        self.last_motion = time.time()

    def update(self):
        """Check for motion and sleep after a period of inactivity."""
        self.motion_detected()

        if self.time_to_sleep():
            self.sleep()

    def time_to_sleep(self):
        return time.time() - self.last_motion > self.sleep_after

    def motion_detected(self):
        """Check if motion over a threshold is detected."""
        motion_count = 0
        while self.sensor.motion_detected:
            motion_count += 1
            # Interrupt the check loop as soon as the threshold is met
            if motion_count > self.motion_threshold:
                self.last_motion = time.time()
                return True
            
        return False
    
    def sleep(self):
        """Put the display to sleep and wait for motion or IR."""
        self.is_awake = False
        hdmi_off()

        while not self.is_awake:
            if self.motion_detected() or self.irw.get_key():
                self.wake()
    
    def wake(self):
        """Wake the display from sleep."""
        self.is_awake = True
        hdmi_on()


def hdmi_off():
    os.system("vcgencmd display_power 0")


def hdmi_on():
    os.system("vcgencmd display_power 1")