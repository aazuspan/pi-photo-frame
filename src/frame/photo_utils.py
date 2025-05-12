from PIL import Image
from pi3d import Texture
from typing import Union
from functools import lru_cache


@lru_cache(maxsize=3)
def load_photo_texture(filepath):
    """Load a photo from a file and return a pi3d.Texture."""
    image = Image.open(filepath)
    image = fix_exif_rotation(image)
    return Texture(image, blend=True, m_repeat=True)


def get_exif_date(image) -> str:
    """
    Return the image date in the format YYYY-MM-DD.
    If no date is available, an empty string is returned.
    """
    exif_data = image.getexif()
    # If present, this will be formatted YYYY:MM:DD HH:mm:SS
    date = exif_data.get(36867, "")
    if date:
        date = date[:10].replace(":", "-")

    return date


def fix_exif_rotation(image):
    """Rotate an image based on its EXIF orientation tag."""
    EXIF_ORIENTATION_TAG = 274
    EXIF_ORIENTATION_DICT = {3: 180, 4: 180, 5: 270, 6: 270, 7: 90, 8: 90}
    
    exif_data = image.getexif()
    exif_orientation: Union[int, None] = exif_data.get(EXIF_ORIENTATION_TAG, None)
    rotate_angle: int = EXIF_ORIENTATION_DICT.get(exif_orientation, 0)

    if rotate_angle:
        image = image.rotate(rotate_angle, expand=True)

    return image
