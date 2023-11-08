from pathlib import Path
from typing import Tuple
import random
from pi3d import Texture
import threading

from .photo import Photo


class PhotoQueue:
    def __init__(self, directory: str, shuffle: bool=True, exts: Tuple[str]=(".jpg", ".jpeg", ".png")):
        self.directory = Path(directory)
        if not self.directory.is_dir():
            raise ValueError(f"{directory} is not a directory!")
        self.shuffle = shuffle
        self.exts = exts
        self.photos = self._get_photos()
        self.idx = 0
        self.preload_thread = threading.Thread(target=self._preload_next)

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

    def load(self) -> Photo:
        """Load the current photo in the queue."""
        if self.preload_thread.is_alive():
            self.preload_thread.join()
        self.preload_thread = threading.Thread(target=self.preload_next)
        self.preload_thread.start()
        
        filepath = self.photos[self.idx].as_posix()
        return Photo(filepath)

    def _preload_next(self):
        """Load the next photo into the cache."""
        next_idx = self.idx + 1
        next_path = self.photos[next_idx].as_posix() if next_idx < len(self.photos) else None
        if not next_path:
            return
        
        Photo(next_path)