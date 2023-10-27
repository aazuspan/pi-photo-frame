from PIL import Image
from pi3d import Texture


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
    rotate_angle = exif_data.get(EXIF_ORIENTATION_TAG, None)

    if not rotate_angle:
        return
    
    return image.rotate(EXIF_ORIENTATION_DICT[rotate_angle], expand=True)