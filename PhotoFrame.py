'''
Digital Photo Frame

Created by Aaron Zuspan, October 2019
Based on pi3d demos https://github.com/pi3d/pi3d_demos

Controls a 2d slideshow of pictures with infrared remote control of playback
and motion-controlled sleep mode.

'''

import os
import time
import random
import logging
import pi3d
from PIL import Image
from classes.Constants import Constants
from classes.IRW import IRW


class PhotoFrame:
    def __init__(self, time_delay=30, fade_time=2, shuffle=True):
        logging.debug('INITIALIZING NEW PHOTO FRAME')
        # Time between frames
        self.time_delay = time_delay
        self.fade_time = fade_time
        # If true, photos are reshuffled every time a slideshow is started or the end of the list is reached
        self.shuffle = shuffle
        self._paused = False
        # Amount of alpha to fade every frame when fading in new photo
        self._delta_alpha = 1.0 / (Constants.FPS * self.fade_time)
        
        self._file_list, self._num_files = self._get_files()
        
        if not self._file_list:
            raise Exception('No valid pictures were found in {}!'.format(Constants.PIC_DIR))
        
        # Initialize the socket that receives IR remote signals
        self.IRW = IRW()
        
        # Current time, used to decide when to change slides
        self.current_time = 0.0
        # Time when the next picture will be displayed
        self.next_time = 0.0
        # List index of current picture
        self.pic_num = 0
        # List index of the next picture
        self.next_pic_num = 0
        # Last time motion was detected. Compared with SLEEP_AFTER to initiate sleep mode
        self.last_motion_time = 0

        # Foreground picture
        self.picture_slide = None
        # Background picture that foreground fades over
        self.background_slide = None
    
    # Resize the current picture to fit the slide (I have no idea how this works)
    def _resize_slide(self):
        self.SLIDE.unif[45:47] = self.SLIDE.unif[42:44]  # transfer front width and height factors to back
        self.SLIDE.unif[51:53] = self.SLIDE.unif[48:50]  # transfer front width and height offsets
        wh_rat = (self.DISPLAY.width * self.picture_slide.iy) / (self.DISPLAY.height * self.picture_slide.ix)
        if (wh_rat > 1.0 and Constants.FIT) or (wh_rat <= 1.0 and not Constants.FIT):
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
        logging.debug('Entering sleep mode')
        # Turn HDMI output off
        os.system("vcgencmd display_power 0")
        # Wait until motion is detected, checking every second
        while not self._is_motion_detected():
            time.sleep(1)
        # Once motion is detected
        self.wake()

    # Wake the display up by turning HDMI back on
    def wake(self):
        logging.debug('Waking from sleep mode')
        # Turn HDMI output on
        os.system("vcgencmd display_power 1")

    # Create the display and start the play loop
    def play(self):
        logging.debug('Initiating play loop')
        self._create()
        self._play_loop()

    # Check if motion is detected and react accordingly
    def check_motion(self):
        if self._is_motion_detected():
            self.last_motion_time = time.time()
        elif self.current_time - self.last_motion_time > Constants.SLEEP_AFTER_SECONDS:
            self.sleep()

    # Check a motion sensor for motion at this moment and return boolean
    def _is_motion_detected(self):
        # TODO: Implement this check once hardware arrives
        return True
    
    # The main playback loop where slides are selected and played
    def _play_loop(self):
        while self.DISPLAY.loop_running():
            self.current_time = time.time()
            if self.current_time > self.next_time and not self._paused:
                self.next_time = self.current_time + self.time_delay
                # Proportion of front image to back
                alpha = 0.0

                # Use current picture as background that next picture will fade over
                self.background_slide = self.picture_slide
                self.picture_slide = None

                while not self.picture_slide:
                    self.pic_num = self.next_pic_num
                    # Create a PIL Image with corrected rotation
                    picture = load_picture(self._file_list[self.pic_num])
                    # Create a texture from the Image
                    self.picture_slide = texture_load(picture)

                    self.next_pic_num += 1

                    # At end of list, wrap back to beginning of list
                    if self.next_pic_num >= self._num_files:
                        # Restart list
                        self.next_pic_num = 0

                        # Reshuffle if requested
                        if self.shuffle:
                            random.shuffle(self._file_list)

                # First run through
                if not self.background_slide:
                    self.background_slide = self.picture_slide

                self.SLIDE.set_textures([self.picture_slide, self.background_slide])
                
                # Resize the picture to fit the slide
                self._resize_slide()

            # BUG: Background slides still show through slightly. Lower FPS makes it worse?
            # Fade alpha in
            if alpha < 1.0:
                alpha += self._delta_alpha
                self.SLIDE.unif[44] = alpha

            self.SLIDE.draw()
            
            # Paused text should stay on screen while paused
            if self._paused:
                # BUG: When play is pressed, pause text still shows over it
                self.TEXT.draw()

            # Check for IR remote commands and react
            self.handle_commands()
            # Check for motion and react
            self.check_motion()

    # Stop the playback loop and kill the display
    def stop(self):
        self.DISPLAY.destroy()
    
    # Create all of the pi3d components that will be used to play the photoframe
    def _create(self):
        logging.debug('Creating pi3d components')
        self.DISPLAY = pi3d.Display.create(frames_per_second=Constants.FPS,
                                      background=Constants.BACKGROUND_COLOR)
        self.CAMERA = pi3d.Camera(is_3d=False)
        self.SHADER = pi3d.Shader("blend_new")
        self.SLIDE = pi3d.Sprite(camera=self.CAMERA, w=self.DISPLAY.width, h=self.DISPLAY.height, z=5.0)
        
        self.SLIDE.set_shader(self.SHADER)
        self.SLIDE.unif[47] = Constants.EDGE_ALPHA

        self.FONT = pi3d.Font(Constants.FONT_FILE, codepoints=Constants.CODEPOINTS, grid_size=7, shadow_radius=4.0,
                 shadow=(0,0,0,128))
        self.TEXT = pi3d.PointText(self.FONT, self.CAMERA, max_chars=200, point_size=50)
        self.TEXTBLOCK = pi3d.TextBlock(x=-self.DISPLAY.width * 0.5 + 50, y=-self.DISPLAY.height * 0.4,
                                   z=0.1, rot=0.0, char_count=199, size=0.99, text_format="{}".format(1),
                                   spacing="F", space=0.02, colour=(1.0, 1.0, 1.0, 1.0))
        self.TEXT.add_text_block(self.TEXTBLOCK)
    
    # Get and return a list of files from the picture directory
    def _get_files(self):
        logging.debug('Collecting files')
        file_list = []
        extensions_list = ['.png', '.jpg', '.jpeg']

        for root, _dirnames, filenames in os.walk(Constants.PIC_DIR):
            for filename in filenames:
                # Get the lowercase file extension of each file
                ext = os.path.splitext(filename)[1].lower()

                if ext in extensions_list and not filename.startswith('.'):
                    file_path_name = os.path.join(root, filename)
                    logging.debug('Adding {} to file list'.format(file_path_name))
                    file_list.append(file_path_name)

        if self.shuffle:
            # Randomize all pictures
            random.shuffle(file_list)
        else:
            # Sort pictures by name
            file_list.sort()

        return file_list, len(file_list)
    
    # Add a text message to the screen
    def text_message(self, message):
        self.TEXTBLOCK.set_text(str(message))
        self.TEXTBLOCK.colouring.set_colour(alpha=0.5)
        self.TEXT.regen()
        self.TEXT.draw()
        
    def toggle_pause(self):
        logging.debug('Toggling pause')
        self._paused = not self._paused

    # Advance time to immediately go to the next slide in line (forward or backward)
    def next_slide(self):
        logging.debug('Skipping to next slide')
        self.next_time = time.time() - 1.0

    # Change slide order to go to previous slide as next slide
    def prev_slide(self):
        logging.debug('Navigating to previous slide')
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
            logging.debug('IR command received: {}'.format(command))
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
            # Exit slideshow
            elif command in ['KEY_EXIT', 'KEY_STOP']:
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
        raise ValueError('Exif data could not be recovered from {}. Please confirm that it is a valid PIL Image.'.format(image))

    try:
        orientation_value = exif_data[Constants.EXIF_ORIENTATION_TAG]
        rotated_image = image.rotate(Constants.EXIF_ORIENTATION_DICT[orientation_value], expand=True)
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


if __name__ == "__main__":
    logging.basicConfig(filename='frameLog.log', format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG)
    frame = PhotoFrame()
    frame.play()
