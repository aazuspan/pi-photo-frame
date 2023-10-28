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

        self.current_time = time.time()
        self.next_time = 0.0

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


    def play(self):
        """Playback loop."""
        while self.display.loop_running():
            self.current_time = time.time()
            if self.current_time > self.next_time and not self._paused:
                self.next_time = self.current_time + self.delay
                # Proportion of front image to back
                alpha = 0.0

                # Use current picture as background that next picture will fade over
                self.background = self.foreground
                self.foreground = None

                while not self.foreground:
                    self.foreground = self.photo_queue.next().load()

                # First run through
                if not self.background:
                    self.background = self.foreground

                self.slide.set_textures([self.foreground, self.background])
                
                # Resize the picture to fit the slide
                self._resize_slide()

            # BUG: "PREVIOUS" will show through when you go back and forth between slides
            # Fade alpha in (avoid overshooting 1.0) and ignore remote and motion
            if alpha + self._delta_alpha < 1.0:
                alpha += self._delta_alpha
                self.slide.unif[44] = alpha
            # Alpha transition is over
            else:
                # Set alpha to fully opaque once fade is finished
                self.slide.unif[44] = 1.0
                # Check for IR remote commands and react
                self.check_irw()

            # Draw the current contents of the frame
            self.slide.draw()
            
            if self.motion_sensor:
                self.motion_sensor.update()
            
            # Paused text should stay on screen while paused
            if self._paused:
                # BUG: When play is pressed, pause text still shows over it
                self.text.draw()

    def stop(self):
        """End the program."""
        if self.motion_sensor:
            self.motion_sensor.stop()
        
        self.display.destroy()

    def _create(self):
        """Create pi3d components."""
        CODEPOINTS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
        self.display = pi3d.Display.create(frames_per_second=constants.FPS, background=constants.BACKGROUND_COLOR)
        camera = pi3d.Camera(is_3d=False)
        shader = pi3d.Shader("blend_new")
        font = pi3d.Font(str(constants.FONT_FILE), grid_size=7, shadow_radius=4.0, codepoints=CODEPOINTS, shadow=(0, 0, 0, 128))

        self.slide = pi3d.Sprite(camera=camera, w=self.display.width, h=self.display.height, z=5.0)
        self.text = pi3d.PointText(font, camera, max_chars=200, point_size=50)
        self.textblock = pi3d.TextBlock(x=-self.display.width * 0.5 + 50, y=-self.display.height * 0.4, z=0.1, rot=0.0, char_count=199, spacing="F", space=0.02)
        
        self.slide.set_shader(shader)
        self.slide.unif[47] = constants.EDGE_ALPHA
        self.text.add_text_block(self.textblock)
    
    # Add a text message to the screen
    def text_message(self, message):
        self.textblock.set_text(str(message))
        self.textblock.colouring.set_colour(alpha=0.5)
        self.text.regen()
        self.text.draw()

    def next_slide(self):
        """Navigate to the next slide."""
        self.next_time = time.time() - 1.0

    def prev_slide(self):
        """Navigate to the previous slide."""
        # TODO: Refactor the photo navigation system
        # The current system advances forward whenever a new slide is loaded,
        # so we have to go back two slides to get to the previous one. 
        self.photo_queue.previous().previous()
        self.next_slide()
            
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
            self.text_message('PLAY')
        elif command == "KEY_PLAYPAUSE":
            self._paused = not self._paused
            self.text_message('PAUSE' if self._paused else 'PLAY')
        elif command in ['KEY_LEFT', 'KEY_REWIND']:
            self.text_message('PREVIOUS')
            self.prev_slide()
        elif command in ['KEY_RIGHT', 'KEY_FORWARD']:
            self.text_message('NEXT')
            self.next_slide()
