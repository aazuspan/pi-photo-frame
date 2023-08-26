import datetime
from pathlib import Path


PIC_DIR = Path('/media/photo_usb')
FONT_FILE = Path('/home/pi/DigitalPhotoFrame/fonts/NotoSans-Regular.ttf')

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
SLEEP_AFTER_SECONDS = 1200

# Seconds between slides
TIME_DELAY = 40
# Seconds of fade time
TIME_FADE = 1.5

# Prevent the display from waking up between midnight and this time
SLEEP_UNTIL_TIME = datetime.time(6, 00)

# Minimum number of motion pulses to count as valid motion (to avoid false positives)
MOTION_THRESHOLD = 50000
