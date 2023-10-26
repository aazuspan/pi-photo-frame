from pathlib import Path
from typing import Tuple
import random
import pi3d
from PIL import Image


class PhotoQueue:
    def __init__(self, directory: str, shuffle: bool=True, exts: Tuple[str]=(".jpg", ".jpeg", ".png")):
        self.directory = Path(directory)
        if not self.directory.is_dir():
            raise ValueError(f"{directory} is not a directory!")
        self.shuffle = shuffle
        self.exts = exts
        self.photos = self._get_photos()
        self.idx = 0

    def _get_photos(self):
        """Generate the photo list."""
        photo_list = []
        for ext in self.exts:
            photo_list += list(self.directory.glob(f"*{ext}"))

        if not photo_list:
            raise FileNotFoundError(f"No photos {self.exts} found in `{self.directory}`!")

        if self.shuffle:
            random.shuffle(photo_list)
        else:
            photo_list.sort()
        
        return photo_list

    def next(self):
        """Advance the queue forward one picture.
        
        The photo list is regenerated after the last photo in the queue.
        """
        self.idx += 1
        if self.idx >= len(self.photos):
            self.photos = self._get_photos()
            self.idx = 0
        return self
    
    def previous(self):
        """Advance the queue backward one picture.
        
        This will stop at the first photo in the queue rather than regenerating.
        """
        self.idx = max(0, self.idx - 1)

        return self

    def load(self) -> pi3d.Texture:
        """Load the current photo in the queue as a Texture."""
        filepath = self.photos[self.idx].as_posix()
        image = Image.open(filepath)
        image = fix_exif_rotation(image)
        return pi3d.Texture(image, blend=True, m_repeat=True)
    

def fix_exif_rotation(image):
    EXIF_ORIENTATION_TAG = 274
    EXIF_ORIENTATION_DICT = {3: 180, 4: 180, 5: 270, 6: 270, 7: 90, 8: 90}

    try:
        exif_data = image._getexif()
        orientation_value = exif_data[EXIF_ORIENTATION_TAG]
        image = image.rotate(EXIF_ORIENTATION_DICT[orientation_value], expand=True)
    except Exception:
        pass

    return image