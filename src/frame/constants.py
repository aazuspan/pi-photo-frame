import datetime
from pathlib import Path


FONT_FILE = Path("./fonts/NotoSans-Regular.ttf")

# Determines how smooth fades are
FPS = 20
FIT = True
# Amount of image reflection on the background
EDGE_ALPHA = 0.0
BACKGROUND_COLOR = (0, 0, 0, 1)

# Turn off display after this many seconds without detecting motion
SLEEP_AFTER_SECONDS = 1200

# Seconds of fade time
TIME_FADE = 1.5

# Prevent the display from waking up between midnight and this time
SLEEP_UNTIL_TIME = datetime.time(6, 00)

# Minimum number of motion pulses to count as valid motion (to avoid false positives)
MOTION_THRESHOLD = 50000
