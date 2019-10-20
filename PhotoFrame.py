import os
import time
import random
import pi3d
from PIL import Image
from classes.Constants import Constants
#from classes.IRW import IRW


'''
Playback variables
'''
time_delay = 3
fade_time = 0.5
shuffle = False
quit = False
paused = False
delta_alpha = 1.0 / (Constants.FPS * fade_time)


# Collect path to all image files to be displayed from the picture directory and return as a list
def get_files():
    global shuffle
    file_list = []
    extensions_list = ['.png', '.jpg', '.jpeg']

    for root, _dirnames, filenames in os.walk(Constants.PIC_DIR):
        for filename in filenames:
            # Get the lowercase file extension of each file
            ext = os.path.splitext(filename)[1].lower()

            if ext in extensions_list and not filename.startswith('.'):
                file_path_name = os.path.join(root, filename)
                file_list.append(file_path_name)

    if shuffle:
        # Randomize all pictures
        random.shuffle(file_list)
    else:
        # Sort pictures by name
        file_list.sort()

    return file_list, len(file_list)


# Load a file or PIL Image as a texture object
def texture_load(filename):
    try:
        texture = pi3d.Texture(filename, blend=True, m_repeat=True)
    except Exception:
        print("Error occured while loading file: {}!".format(filename))
        texture = None
    return texture


# Take a PIL Image, rotate it based on Exif orientation data, and return it
def fix_rotation(image):
    try:
        exif_data = image._getexif()
    # If the image doesn't have a _getexif method, it isn't valid
    except AttributeError:
        raise ValueError('Exif data could not be recovered from {}. Please confirm that it is a valid PIL Image.'.format(image))
    try:
        orientation_value = exif_data[Constants.EXIF_ORIENTATION_TAG]
    # If the image's exif data doesn't have an orientation value
    except (IndexError, TypeError):
        return image

    try:
        rotated_image = image.rotate(Constants.EXIF_ORIENTATION_DICT[orientation_value], expand=True)
    # If the orientation value isn't in the dictionary keys, it is either invalid or not rotated
    except KeyError:
        return image

    return rotated_image


# Load a picture as a PIL image, correct rotation, and return it
def load_picture(picture_path):
    picture = Image.open(picture_path)
    # Rotate the picture based on EXIF data if necessary
    picture = fix_rotation(picture)

    return picture


def toggle_pause():
    global paused
    paused = not paused


def next_slide():
    return time.time() - 1.0


def prev_slide(next_pic_num):
    next_pic_num -= 2
    if next_pic_num < -1:
        next_pic_num = -1
    return next_pic_num

# Initialize the socket that receives IR remote signals
#IRW = IRW()

DISPLAY = pi3d.Display.create(frames_per_second=Constants.FPS,
                              background=Constants.BACKGROUND_COLOR)
CAMERA = pi3d.Camera(is_3d=False)
shader = pi3d.Shader("blend_new")
slide = pi3d.Sprite(camera=CAMERA, w=DISPLAY.width, h=DISPLAY.height, z=5.0)
slide.set_shader(shader)
slide.unif[47] = Constants.EDGE_ALPHA
KEYBOARD = pi3d.Keyboard()

pic_list, number_pictures = get_files()
if not pic_list:
    raise Exception('No valid pictures were found in {}!'.format(Constants.PIC_DIR))

# Time when the next picture will be displayed
next_time = 0.0
# List index of the next picture
next_pic_num = 0
# Number of times the entire picture list has been shown
loop_num = 0

picture_slide = None
background_slide = None

while DISPLAY.loop_running():
    current_time = time.time()
    if current_time > next_time and not paused:
        next_time = current_time + time_delay
        # Proportion of front image to back
        alpha = 0.0

        # Use current picture as background that next picture will fade over
        background_slide = picture_slide
        picture_slide = None

        while not picture_slide:
            pic_num = next_pic_num
            # Create a PIL Image with corrected rotation
            picture = load_picture(pic_list[pic_num])
            # Create a texture from the Image
            picture_slide = texture_load(picture)

            next_pic_num += 1

            # At end of list, wrap back to beginning of list
            if next_pic_num >= len(pic_list):
                # Restart list
                next_pic_num = 0
                loop_num += 1

                # Reshuffle if requested
                if shuffle and loop_num >= Constants.RESHUFFLE_AFTER:
                    loop_num = 0
                    random.shuffle(pic_list)

        # First run through
        if not background_slide:
            background_slide = picture_slide

        slide.set_textures([picture_slide, background_slide])

        slide.unif[45:47] = slide.unif[42:44]  # transfer front width and height factors to back
        slide.unif[51:53] = slide.unif[48:50]  # transfer front width and height offsets
        wh_rat = (DISPLAY.width * picture_slide.iy) / (DISPLAY.height * picture_slide.ix)
        if (wh_rat > 1.0 and Constants.FIT) or (wh_rat <= 1.0 and not Constants.FIT):
            sz1, sz2, os1, os2 = 42, 43, 48, 49
        else:
            sz1, sz2, os1, os2 = 43, 42, 49, 48
            wh_rat = 1.0 / wh_rat
        slide.unif[sz1] = wh_rat
        slide.unif[sz2] = 1.0
        slide.unif[os1] = (wh_rat - 1.0) * 0.5
        slide.unif[os2] = 0.0

    # Fade alpha in
    if alpha < 1.0:
        alpha += delta_alpha
        slide.unif[44] = alpha

    slide.draw()

    # Check for IR remote signals
    #command = IRW.get_key()
    command = None
    # If an IR remote signal is detected
    if command:
        # Toggle pause
        if command in ['KEY_PLAY', 'KEY_PLAYPAUSE']:
            toggle_pause()
        # Previous slide
        elif command in ['KEY_LEFT', 'KEY_REWIND']:
            next_pic_num = prev_slide(next_pic_num)
        # Next slide
        elif command in ['KEY_RIGHT', 'KEY_FORWARD']:
            next_time = next_slide()
        # Exit slideshow
        elif command in ['KEY_EXIT', 'KEY_STOP']:
            break

    key = KEYBOARD.read()
    key = -1
    if key != -1:
        next_time = next_slide()
    # Exit condition
    if key == 27 or quit:
        break
    # Toggle play/pause
    if key == ord(' '):
        toggle_pause()
    # Previous slide
    if key == ord('s'):
        next_pic_num = prev_slide(next_pic_num)

KEYBOARD.close()
DISPLAY.destroy()
