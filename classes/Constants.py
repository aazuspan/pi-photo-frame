import os
from pathlib import Path


class Constants:
    HOME_DIR = str(Path.home())
    PIC_DIR = os.path.join(HOME_DIR, 'Pictures')
    FONT_FILE = os.path.join('fonts', 'NotoSans-Regular.ttf')

    FPS = 20
    FIT = True
    EDGE_ALPHA = 0
    BACKGROUND_COLOR = (0, 0, 0, 1)
    RESHUFFLE_AFTER = 1
    CODEPOINTS = '1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ., _-/'

    # The exif tag number for orientation
    EXIF_ORIENTATION_TAG = 274
    # Exif orientation values and corresponding degree rotation
    EXIF_ORIENTATION_DICT = {3: 180, 4: 180, 5: 270, 6: 270, 7: 90, 8: 90}
