import logging
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)


class EnhancementsModule:
    def apply(self, image: Image.Image, brightness=1.0, contrast=1.0,
              sharpness=1.0, saturation=1.0, color_balance=1.0) -> Image.Image:
        try:
            img = image.copy()
            img = ImageEnhance.Brightness(img).enhance(brightness)
            img = ImageEnhance.Contrast(img).enhance(contrast)
            img = ImageEnhance.Sharpness(img).enhance(sharpness)
            img = ImageEnhance.Color(img).enhance(saturation)
            # Color balance via second Color pass
            img = ImageEnhance.Color(img).enhance(color_balance)
            return img
        except Exception as e:
            logger.error(f"Enhancement error: {e}")
            return image
