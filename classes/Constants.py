import os
from pathlib import Path


class Constants:
    PIC_DIR = os.path.join('/media', 'pi', 'MYKEYCHAIN')
    FONT_FILE = os.path.join('fonts', 'NotoSans-Regular.ttf')

    # Determines how smooth fades are
    FPS = 10
    FIT = True
    # Amount of image reflection on the background
    EDGE_ALPHA = 0.0
    BACKGROUND_COLOR = (0, 0, 0, 1)
    CODEPOINTS = '1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ., _-/'

    # The exif tag number for orientation
    EXIF_ORIENTATION_TAG = 274
    # Exif orientation values and corresponding degree rotation
    EXIF_ORIENTATION_DICT = {3: 180, 4: 180, 5: 270, 6: 270, 7: 90, 8: 90}
