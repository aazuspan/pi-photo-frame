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

import os
import time
import datetime
import random
import logging
from pathlib import Path
import pi3d
from gpiozero import MotionSensor
from PIL import Image
from . import constants
from .irw import IRW


class PhotoFrame:
    def __init__(self, photo_dir, delay, shuffle=True):
        logging.info('INITIALIZING NEW PHOTO FRAME')
        self.photo_dir = Path(photo_dir)
        self.delay = delay
        # If true, photos are reshuffled every time a slideshow is started or the end of the list is reached
        self.shuffle = shuffle
        self._paused = False
        self.is_awake = True
        # Create a motion sensor on GPIO pin 15. Queue_len determines sensitivity (more = less sensitive)
        self.motionsensor = MotionSensor(15, queue_len=30)
        # Amount of alpha to fade every frame when fading in new photo
        self._delta_alpha = 1.0 / (constants.FPS * constants.TIME_FADE)
        
        self._file_list = self._get_files()
        self._num_files = len(self._file_list)
        
        # Initialize the socket that receives IR remote signals
        self.IRW = IRW()
        
        # Current time, used to decide when to change slides
        self.current_time = time.time()
        # Time when the next picture will be displayed
        self.next_time = 0.0
        # List index of current picture
        self.pic_num = 0
        # List index of the next picture
        self.next_pic_num = 0
        # Last time motion was detected. Compared with SLEEP_AFTER to initiate sleep mode
        self.last_motion_time = time.time()

        # Foreground picture
        self.picture_slide = None
        # Background picture that foreground fades over
        self.background_slide = None
    
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

    # Turn HDMI off to put display monitor to sleep. Stay in this loop until motion is detected
    def sleep(self):
        self.is_awake = False
        logging.info('Entering sleep mode')
        # Turn HDMI output off
        os.system("vcgencmd display_power 0")

        # Continue sleeping until motion is detected
        while not self.is_awake:
            # Check for IR commands that would wake up the display
            self.handle_commands()

            # Check for motion that would wake up the display
            if self.is_significant_motion_detected():
                self.wake()

    # Wake the display up by turning HDMI back on
    def wake(self, force=False):
        current_time = datetime.datetime.now().time()
        if current_time >= constants.SLEEP_UNTIL_TIME or force:
            self.is_awake = True
            logging.info('Waking from sleep mode')
            # Turn HDMI output on
            os.system("vcgencmd display_power 1")
            # Update motion time so it doesn't immediately go back to sleep
            self.last_motion_time = time.time()
        else:
            logging.info('Tried to wake from sleep mode but current time is within the sleep_until time.')

    # Create the display and start the play loop
    def play(self):
        logging.info('Initiating play loop')
        # Activate HDMI on the Pi
        os.system("vcgencmd display_power 1")
        self._create()
        self._play_loop()

    # Check for motion and update last motion time if detected
    def update_motion_time(self):
        if self.is_significant_motion_detected():
            self.last_motion_time = time.time()

    # Check last motion time and decide whether it is time to sleep
    def is_time_to_sleep(self):
        return self.current_time - self.last_motion_time > constants.SLEEP_AFTER_SECONDS

    # Called when motion is detected. Return whether the motion lasts long enough to meet the threshold
    def is_significant_motion_detected(self):
        motion_count = 0
        while self.motionsensor.motion_detected:
            motion_count += 1
            # Interrupt the check loop as soon as the threshold is met
            if motion_count > constants.MOTION_THRESHOLD:
                return True
        # Motion threshold wasn't met
        return False

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
                    self.pic_num = self.next_pic_num
                    picture = load_picture(self._file_list[self.pic_num])
                    self.picture_slide = texture_load(picture)

                    self.next_pic_num += 1

                    # At end of list, wrap back to beginning of list
                    if self.next_pic_num >= self._num_files:
                        self.next_pic_num = 0

                        if self.shuffle:
                            random.shuffle(self._file_list)

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
                # Check for motion and update the last motion time
                self.update_motion_time()
                # Decide whether to sleep based on last motion time and current time
                if self.is_time_to_sleep():
                    self.sleep()

            # Draw the current contents of the frame
            self.SLIDE.draw()
            
            # Paused text should stay on screen while paused
            if self._paused:
                # BUG: When play is pressed, pause text still shows over it
                self.TEXT.draw()

    # Check if exit key is hit enough times to stop the program
    def is_exit_confirmed(self):
        start_time = time.time()
        # How long will exit keys be accepted for?
        check_seconds = 2
        # Number of times exit key has been hit
        current_exit_count = 0
        # Number of times exit key must be hit to close (not counting the exit key that triggered this check)
        required_exit_count = 2

        # Check time
        while time.time() < start_time + check_seconds:
            # Look for IR commands
            command = self.IRW.get_key()
            if command == 'KEY_EXIT':
                current_exit_count += 1
                if current_exit_count >= required_exit_count:
                    return True
        # Check time passed without exit key being hit enough
        return False

    # End the program
    def stop(self):
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

        self.FONT = pi3d.Font(str(constants.FONT_FILE), codepoints=constants.CODEPOINTS, grid_size=7, shadow_radius=4.0,
                              shadow=(0, 0, 0, 128))
        self.TEXT = pi3d.PointText(self.FONT, self.CAMERA, max_chars=200, point_size=50)
        self.TEXTBLOCK = pi3d.TextBlock(x=-self.DISPLAY.width * 0.5 + 50, y=-self.DISPLAY.height * 0.4,
                                        z=0.1, rot=0.0, char_count=199, size=0.99, text_format="{}".format(1),
                                        spacing="F", space=0.02, colour=(1.0, 1.0, 1.0, 1.0))
        self.TEXT.add_text_block(self.TEXTBLOCK)
    
    # Get and return a list of files from the picture directory
    def _get_files(self):
        logging.info('Collecting files')
        extensions_list = ['.png', '.jpg', '.jpeg']
        file_list = []
        for ext in extensions_list:
            file_list += list(self.photo_dir.glob("*{}".format(ext)))

        if self.shuffle:
            # Randomize all pictures
            random.shuffle(file_list)
        else:
            # Sort pictures by name
            file_list.sort()
        
        if file_list:
            raise Exception('No valid pictures were found in {}!'.format(self.photo_dir))
        
        return file_list
    
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

    # Change slide order to go to previous slide as next slide
    def prev_slide(self):
        self.next_pic_num -= 2
        if self.next_pic_num < -1:
            self.next_pic_num = -1
            
    # Check for IR remote commands and handle them
    def handle_commands(self):
        # Check for IR remote signals
        command = self.IRW.get_key()

        # TODO: Allow navigating next and previous even if paused
        # If an IR remote signal is detected
        if command:
            logging.info('IR command received: {}'.format(command))

            # Wake from sleep but don't execute the command
            if not self.is_awake:
                self.wake(force=True)

            # Execute the command
            else:
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
                elif command == 'KEY_STOP':
                    self.sleep()
                # Exit slideshow
                elif command == 'KEY_EXIT':
                    # If the exit key is pressed repeatedly
                    if self.is_exit_confirmed():
                        self.stop()


# Load a file or PIL Image as a texture object
def texture_load(filename):
    logging.debug('Loading texture from {}'.format(filename))
    try:
        texture = pi3d.Texture(filename, blend=True, m_repeat=True)
    except Exception:
        print("Error occured while loading file: {}!".format(filename))
        texture = None
    return texture


# Take a PIL Image, rotate it based on Exif orientation data, and return it
def _fix_rotation(image):
    try:
        exif_data = image._getexif()
    # If the image doesn't have a _getexif method, it isn't valid
    except AttributeError:
        raise ValueError('Exif data could not be recovered from {}. Please confirm that it is a valid PIL Image.'.
                         format(image))

    try:
        orientation_value = exif_data[constants.EXIF_ORIENTATION_TAG]
        rotated_image = image.rotate(constants.EXIF_ORIENTATION_DICT[orientation_value], expand=True)
        return rotated_image
    # If the image doesn't have exif data or the orientation value isn't in the dictionary keys
    except (KeyError, TypeError, IndexError):
        return image


# Load a picture as a PIL image, correct rotation, and return it
def load_picture(picture_path):
    logging.debug('Loading picture {}'.format(picture_path))
    picture = Image.open(picture_path)
    # Rotate the picture based on EXIF data if necessary
    picture = _fix_rotation(picture)

    return picture
