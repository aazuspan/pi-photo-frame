import os
from pathlib import Path


class Constants:
    PIC_DIR = os.path.join('/media', 'photo_usb')
    FONT_FILE = os.path.join('/home', 'pi', 'DigitalPhotoFrame', 'fonts', 'NotoSans-Regular.ttf')

    # Determines how smooth fades are
    FPS = 20
    FIT = True
    # Amount of image reflection on the background
    EDGE_ALPHA = 0.0
    BACKGROUND_COLOR = (0, 0, 0, 1)
    CODEPOINTS = '1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ., _-/'

    # The exif tag number for orientation
    EXIF_ORIENTATION_TAG = 274
    # Exif orientation values and corresponding degree rotation
    EXIF_ORIENTATION_DICT = {3: 180, 4: 180, 5: 270, 6: 270, 7: 90, 8: 90}

    # Turn off display after this many seconds without detecting motion
    SLEEP_AFTER_SECONDS = 1800
    
    # Seconds between slides
    TIME_DELAY = 40
    # Seconds of fade time
    TIME_FADE = 2
