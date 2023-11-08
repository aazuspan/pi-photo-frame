from PIL import Image
from pi3d import Texture
from typing import Union
from functools import lru_cache
from colorthief import ColorThief


class Photo:
    def __init__(self, filepath):
        self.image = _load_cached_image(filepath)

    def get_palette(self):
        """Return a list of RGB tuples representing the dominant colors in the photo."""
        return ColorThief(self.image).get_palette(color_count=3, quality=10)
        
    def load_texture(self) -> Texture:
        return Texture(self.image, blend=True, m_repeat=True)


@lru_cache(maxsize=3)
def _load_cached_image(filepath) -> Image:
    """Load a photo from a file and return a pi3d.Texture."""
    return fix_exif_rotation(Image.open(filepath))


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