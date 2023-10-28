from pathlib import Path

# Font path relative to the CLI module
FONT_FILE = Path(__file__).parent.parent.parent / "fonts/opensans.ttf"
CODEPOINTS = u'°abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_+=~`[]{}|\:;"\'<>,.?/ üöäÜÖÄß'

# Determines how smooth fades are
FPS = 20
FIT = True
# Amount of image reflection on the background
EDGE_ALPHA = 0.0
BACKGROUND_COLOR = (0, 0, 0, 1)

# Seconds of fade time
TIME_FADE = 1.5
