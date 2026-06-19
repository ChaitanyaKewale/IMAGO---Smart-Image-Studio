import logging
from PIL import Image, ImageOps
import os

logger = logging.getLogger(__name__)


class ImageProcessor:
    def __init__(self):
        self.original_image = None
        self.current_image = None
        self.undo_stack = []
        self.redo_stack = []
        self.current_path = None

    def load_image(self, path):
        try:
            img = Image.open(path).convert("RGBA")
            self.original_image = img.copy()
            self.current_image = img.copy()
            self.current_path = path
            self.undo_stack.clear()
            self.redo_stack.clear()
            return True
        except Exception as e:
            logger.error(f"Load error: {e}")
            return False

    def _push_undo(self):
        if self.current_image:
            self.undo_stack.append(self.current_image.copy())
            if len(self.undo_stack) > 30:
                self.undo_stack.pop(0)
            self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(self.current_image.copy())
            self.current_image = self.undo_stack.pop()
            return True
        return False

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.current_image.copy())
            self.current_image = self.redo_stack.pop()
            return True
        return False

    def resize(self, width, height, keep_aspect=True):
        if not self.current_image:
            return False
        self._push_undo()
        try:
            if keep_aspect:
                self.current_image.thumbnail((width, height), Image.LANCZOS)
            else:
                self.current_image = self.current_image.resize((width, height), Image.LANCZOS)
            return True
        except Exception as e:
            logger.error(f"Resize error: {e}")
            return False

    def crop(self, left, top, right, bottom):
        if not self.current_image:
            return False
        self._push_undo()
        try:
            self.current_image = self.current_image.crop((left, top, right, bottom))
            return True
        except Exception as e:
            logger.error(f"Crop error: {e}")
            return False

    def rotate(self, angle):
        if not self.current_image:
            return False
        self._push_undo()
        try:
            self.current_image = self.current_image.rotate(angle, expand=True)
            return True
        except Exception as e:
            logger.error(f"Rotate error: {e}")
            return False

    def flip(self, direction):
        if not self.current_image:
            return False
        self._push_undo()
        try:
            if direction == "horizontal":
                self.current_image = ImageOps.mirror(self.current_image)
            else:
                self.current_image = ImageOps.flip(self.current_image)
            return True
        except Exception as e:
            logger.error(f"Flip error: {e}")
            return False

    def reset_to_original(self):
        if self.original_image:
            self._push_undo()
            self.current_image = self.original_image.copy()
            return True
        return False

    def save(self, path, quality=95, fmt=None):
        if not self.current_image:
            return False
        try:
            ext = fmt or os.path.splitext(path)[1].lower().strip(".")
            ext = ext.upper()
            if ext in ("JPG", "JPEG"):
                img = self.current_image.convert("RGB")
                img.save(path, format="JPEG", quality=quality)
            elif ext == "PNG":
                self.current_image.save(path, format="PNG")
            elif ext == "WEBP":
                self.current_image.save(path, format="WEBP", quality=quality)
            elif ext == "BMP":
                self.current_image.convert("RGB").save(path, format="BMP")
            elif ext == "TIFF":
                self.current_image.save(path, format="TIFF")
            else:
                self.current_image.save(path)
            return True
        except Exception as e:
            logger.error(f"Save error: {e}")
            return False

    def get_thumbnail(self, size=(300, 300)):
        if not self.current_image:
            return None
        img = self.current_image.copy()
        img.thumbnail(size, Image.LANCZOS)
        return img
