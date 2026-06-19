import logging
from PIL import Image

logger = logging.getLogger(__name__)


class BackgroundRemovalModule:
    def remove(self, image: Image.Image, bg_color=None) -> Image.Image:
        """
        Remove background using rembg.
        bg_color: None = transparent, (R,G,B) = solid color
        """
        try:
            from rembg import remove as rembg_remove
            png = image.convert("RGBA")
            result = rembg_remove(png)

            if bg_color is not None:
                bg = Image.new("RGBA", result.size, (*bg_color, 255))
                bg.paste(result, mask=result.split()[3])
                return bg
            return result
        except ImportError:
            logger.error("rembg not installed")
            return self._fallback(image, bg_color)
        except Exception as e:
            logger.error(f"Background removal error: {e}")
            return image

    def _fallback(self, image, bg_color):
        """Simple GrabCut fallback if rembg is unavailable."""
        try:
            import cv2
            import numpy as np
            rgb = np.array(image.convert("RGB"))
            mask = np.zeros(rgb.shape[:2], np.uint8)
            h, w = rgb.shape[:2]
            rect = (10, 10, w - 20, h - 20)
            bgd = np.zeros((1, 65), np.float64)
            fgd = np.zeros((1, 65), np.float64)
            cv2.grabCut(rgb, mask, rect, bgd, fgd, 5, cv2.GC_INIT_WITH_RECT)
            mask2 = np.where((mask == 2) | (mask == 0), 0, 255).astype("uint8")
            rgba = np.dstack([rgb, mask2])
            result = Image.fromarray(rgba, "RGBA")
            if bg_color:
                bg = Image.new("RGBA", result.size, (*bg_color, 255))
                bg.paste(result, mask=result.split()[3])
                return bg
            return result
        except Exception as e:
            logger.error(f"Fallback BG removal error: {e}")
            return image
