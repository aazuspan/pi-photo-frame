'''
Digital Photo Frame

Created by Aaron Zuspan, October 2019
Based on pi3d demos https://github.com/pi3d/pi3d_demos

Controls a 2d slideshow of pictures with infrared remote control of playback
and motion-controlled sleep mode.

GPIO pins:
    Pin 15: PIR motion sensor
    Pin 18: IR receiver (defined in LIRC settings)
'''

import time
import logging
import pi3d
import threading
from typing import Union
from . import constants
from .irw import IRW
from .photo_queue import PhotoQueue
from .motion_sensor import MotionSensor


class PhotoFrame:
    def __init__(self, photo_dir, delay, shuffle=True, motion_gpio=None, use_irw=False):
        logging.info('INITIALIZING NEW PHOTO FRAME')
        self.delay = delay
        self._paused = False
        
        self.irw = IRW() if use_irw else None
        self.photo_queue = PhotoQueue(directory=photo_dir, shuffle=shuffle)
        self.motion_sensor = MotionSensor(motion_gpio) if motion_gpio else None
        
        # Amount of alpha to fade every frame when fading in new photo
        self._delta_alpha = 1.0 / (constants.FPS * constants.TIME_FADE)
        self.foreground_alpha = 0.0

        self.current_time = time.time()
        self.next_time = 0.0
        self.text_thread = threading.Timer(0.0, self.clear_text)

        self.foreground = None
        self.background = None
    
        self._create()

    def _resize_slide(self):
        """Resize the current picture to fit the slide."""
        self.slide.unif[45:47] = self.slide.unif[42:44]  # transfer front width and height factors to back
        self.slide.unif[51:53] = self.slide.unif[48:50]  # transfer front width and height offsets
        wh_rat = (self.display.width * self.foreground.iy) / (self.display.height * self.foreground.ix)
        if (wh_rat > 1.0 and constants.FIT) or (wh_rat <= 1.0 and not constants.FIT):
            sz1, sz2, os1, os2 = 42, 43, 48, 49
        else:
            sz1, sz2, os1, os2 = 43, 42, 49, 48
            wh_rat = 1.0 / wh_rat
        self.slide.unif[sz1] = wh_rat
        self.slide.unif[sz2] = 1.0
        self.slide.unif[os1] = (wh_rat - 1.0) * 0.5
        self.slide.unif[os2] = 0.0

    def update_slide(self):
        """Set the foreground and background for a new slide."""
        self.background = self.foreground
        self.foreground = None

        while not self.foreground:
            self.foreground = self.photo_queue.load()

        # First run through
        if not self.background:
            self.background = self.foreground

        self.slide.set_textures([self.foreground, self.background])            
        self._resize_slide()
        self.next_time = self.current_time + self.delay

    def update_alpha(self):
        if self.foreground_alpha >= 1.0:
            return

        self.foreground_alpha = min(self.foreground_alpha + self._delta_alpha, 1.0)
        self.slide.unif[44] = self.foreground_alpha

    def play(self):
        """Playback loop."""
        while self.display.loop_running():
            self.update_alpha()
            self.slide.draw()
            self.text.draw()
            self.check_irw()

            self.current_time = time.time()
            if self.current_time > self.next_time and not self._paused:
                self.foreground_alpha = 0.0
                self.next_slide()
                        
            if self.motion_sensor:
                self.motion_sensor.update()

    def stop(self):
        """End the program."""
        if self.motion_sensor:
            self.motion_sensor.stop()
        
        self.display.destroy()

    def _create(self):
        """Create pi3d components."""
        self.display = pi3d.Display.create(frames_per_second=constants.FPS, background=constants.BACKGROUND_COLOR)
        camera = pi3d.Camera(is_3d=False)
        shader = pi3d.Shader("blend_new")
        font = pi3d.Font(str(constants.FONT_FILE), codepoints=constants.CODEPOINTS, shadow_radius=4.0, shadow=(0, 0, 0, 128))

        self.slide = pi3d.Sprite(camera=camera, w=self.display.width, h=self.display.height, z=5.0)
        self.text = pi3d.PointText(font, camera, max_chars=200, point_size=50)
        self.textblock = pi3d.TextBlock(x=-self.display.width * 0.5 + 50, y=-self.display.height * 0.4, z=0.1, rot=0.0, char_count=199, spacing="F", space=0.02)
        
        self.slide.set_shader(shader)
        self.slide.unif[47] = constants.EDGE_ALPHA
        self.text.add_text_block(self.textblock)
        self.textblock.set_text("")
    
    def clear_text(self):
        """Clear text from the screen."""
        self.textblock.colouring.set_colour(alpha=0.0)

    def display_text(self, message, duration: Union[float, None]=2.0):
        """Display text on the screen."""
        self.textblock.set_text(str(message))
        self.text.regen()
        self.text.draw()

        self.text_thread.cancel()
        if duration is not None:
            self.text_thread = threading.Timer(duration, self.clear_text)
            self.text_thread.start()

    def next_slide(self):
        """Navigate to the next slide."""
        self.photo_queue.next()
        self.update_slide()

    def prev_slide(self):
        """Navigate to the previous slide."""
        self.photo_queue.previous()
        self.update_slide()
            
    def check_irw(self):
        """Check for IR remote commands and handle them."""
        if not self.irw:
            return
        
        command = self.irw.get_key()
        if not command:
            return
        
        logging.info('IR command received: {}'.format(command))

        if command == "KEY_PLAY":
            self._paused = False
            self.display_text('PLAY')
        elif command == "KEY_PLAYPAUSE":
            self._paused = not self._paused
            self.display_text('PAUSE' if self._paused else 'PLAY')
        elif command in ['KEY_LEFT', 'KEY_REWIND']:
            self.display_text('PREVIOUS')
            self.prev_slide()
        elif command in ['KEY_RIGHT', 'KEY_FORWARD']:
            self.display_text('NEXT')
            self.next_slide()
        elif command == "KEY_UP":
            img_name = self.photo_queue.photos[self.photo_queue.idx].name
            self.display_text(img_name, duration=10)