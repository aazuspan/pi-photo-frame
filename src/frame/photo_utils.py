from PIL import Image
from pi3d import Texture
from typing import Union
from functools import lru_cache


@lru_cache(maxsize=2)
def load_photo_texture(filepath):
    """Load a photo from a file and return a pi3d.Texture."""
    image = Image.open(filepath)
    image = fix_exif_rotation(image)
    return Texture(image, blend=True, m_repeat=True)


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