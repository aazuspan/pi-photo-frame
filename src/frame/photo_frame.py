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
    def __init__(self, photo_dir, delay, shuffle=True, motion_gpio=None):
        logging.info('INITIALIZING NEW PHOTO FRAME')
        self.delay = delay
        self._paused = False
        
        self.irw = IRW()
        self.photo_queue = PhotoQueue(directory=photo_dir, shuffle=shuffle)
        self.motion_sensor = MotionSensor(motion_gpio, irw=self.irw) if motion_gpio else None
        
        # Amount of alpha to fade every frame when fading in new photo
        self._delta_alpha = 1.0 / (constants.FPS * constants.TIME_FADE)

        # Current time, used to decide when to change slides
        self.current_time = time.time()
        # Time when the next picture will be displayed
        self.next_time = 0.0

        # Foreground picture
        self.picture_slide = None
        # Background picture that foreground fades over
        self.background_slide = None
    
        self._create()
        self._play_loop()

    # Resize the current picture to fit the slide (I have no idea how this works)
    def _resize_slide(self):
        self.SLIDE.unif[45:47] = self.SLIDE.unif[42:44]  # transfer front width and height factors to back
        self.SLIDE.unif[51:53] = self.SLIDE.unif[48:50]  # transfer front width and height offsets
        wh_rat = (self.DISPLAY.width * self.picture_slide.iy) / (self.DISPLAY.height * self.picture_slide.ix)
        if (wh_rat > 1.0 and constants.FIT) or (wh_rat <= 1.0 and not constants.FIT):
            sz1, sz2, os1, os2 = 42, 43, 48, 49
        else:
            sz1, sz2, os1, os2 = 43, 42, 49, 48
            wh_rat = 1.0 / wh_rat
        self.SLIDE.unif[sz1] = wh_rat
        self.SLIDE.unif[sz2] = 1.0
        self.SLIDE.unif[os1] = (wh_rat - 1.0) * 0.5
        self.SLIDE.unif[os2] = 0.0


    # The main playback loop where slides are selected and played
    def _play_loop(self):
        while self.DISPLAY.loop_running():
            self.current_time = time.time()
            if self.current_time > self.next_time and not self._paused:
                self.next_time = self.current_time + self.delay
                # Proportion of front image to back
                alpha = 0.0

                # Use current picture as background that next picture will fade over
                self.background_slide = self.picture_slide
                self.picture_slide = None

                while not self.picture_slide:
                    self.picture_slide = self.photo_queue.next().load()

                # First run through
                if not self.background_slide:
                    self.background_slide = self.picture_slide

                self.SLIDE.set_textures([self.picture_slide, self.background_slide])
                
                # Resize the picture to fit the slide
                self._resize_slide()

            # BUG: "PREVIOUS" will show through when you go back and forth between slides
            # Fade alpha in (avoid overshooting 1.0) and ignore remote and motion
            if alpha + self._delta_alpha < 1.0:
                alpha += self._delta_alpha
                self.SLIDE.unif[44] = alpha
            # Alpha transition is over
            else:
                # Set alpha to fully opaque once fade is finished
                self.SLIDE.unif[44] = 1.0
                # Check for IR remote commands and react
                self.handle_commands()

            # Draw the current contents of the frame
            self.SLIDE.draw()
            
            if self.motion_sensor:
                self.motion_sensor.update()
            
            # Paused text should stay on screen while paused
            if self._paused:
                # BUG: When play is pressed, pause text still shows over it
                self.TEXT.draw()

    # End the program
    def stop(self):
        if self.motion_sensor:
            self.motion_sensor.wake()
        
        self.DISPLAY.destroy()

    # Create all of the pi3d components that will be used to play the photoframe
    def _create(self):
        logging.info('Creating pi3d components')
        self.DISPLAY = pi3d.Display.create(frames_per_second=constants.FPS,
                                           background=constants.BACKGROUND_COLOR)
        self.CAMERA = pi3d.Camera(is_3d=False)
        self.SHADER = pi3d.Shader("blend_new")
        self.SLIDE = pi3d.Sprite(camera=self.CAMERA, w=self.DISPLAY.width, h=self.DISPLAY.height, z=5.0)
        
        self.SLIDE.set_shader(self.SHADER)
        self.SLIDE.unif[47] = constants.EDGE_ALPHA

        self.FONT = pi3d.Font(str(constants.FONT_FILE), grid_size=7, shadow_radius=4.0,
                              codepoints="ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890", shadow=(0, 0, 0, 128))
        self.TEXT = pi3d.PointText(self.FONT, self.CAMERA, max_chars=200, point_size=50)
        self.TEXTBLOCK = pi3d.TextBlock(x=-self.DISPLAY.width * 0.5 + 50, y=-self.DISPLAY.height * 0.4,
                                        z=0.1, rot=0.0, char_count=199, size=0.99, text_format="{}".format(1),
                                        spacing="F", space=0.02, colour=(1.0, 1.0, 1.0, 1.0))
        self.TEXT.add_text_block(self.TEXTBLOCK)
    
    # Add a text message to the screen
    def text_message(self, message):
        self.TEXTBLOCK.set_text(str(message))
        self.TEXTBLOCK.colouring.set_colour(alpha=0.5)
        self.TEXT.regen()
        self.TEXT.draw()
        
    def toggle_pause(self):
        self._paused = not self._paused

    # Advance time to immediately go to the next slide in line (forward or backward)
    def next_slide(self):
        self.next_time = time.time() - 1.0

    def prev_slide(self):
        # TODO: Refactor the photo navigation system
        # The current system advances forward whenever a new slide is loaded,
        # so we have to go back two slides to get to the previous one. 
        self.photo_queue.previous().previous()
            
    # Check for IR remote commands and handle them
    def handle_commands(self):
        # Check for IR remote signals
        command = self.irw.get_key()

        # TODO: Allow navigating next and previous even if paused
        # If an IR remote signal is detected
        if command:
            logging.info('IR command received: {}'.format(command))

            # Toggle pause
            if command in ['KEY_PLAY', 'KEY_PLAYPAUSE']:
                if self._paused:
                    self.text_message('PLAY')
                else:
                    self.text_message('PAUSE')
                self.toggle_pause()
            # Previous slide
            elif command in ['KEY_LEFT', 'KEY_REWIND']:
                self.text_message('PREVIOUS')
                # Set the previous slide as next
                self.prev_slide()
                # Go to it immediately
                self.next_slide()
            # Next slide
            elif command in ['KEY_RIGHT', 'KEY_FORWARD']:
                self.text_message('NEXT')
                self.next_slide()
