import logging
from PIL import Image, ImageFilter, ImageOps, ImageEnhance
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class FiltersModule:
    FILTERS = [
        "Blur", "Gaussian Blur", "Sharpen", "Edge Detection",
        "Emboss", "Smooth", "Contour", "Detail",
        "Black & White", "Vintage", "Sketch"
    ]

    def apply(self, image: Image.Image, filter_name: str) -> Image.Image:
        try:
            method = {
                "Blur": self._blur,
                "Gaussian Blur": self._gaussian_blur,
                "Sharpen": self._sharpen,
                "Edge Detection": self._edge_detection,
                "Emboss": self._emboss,
                "Smooth": self._smooth,
                "Contour": self._contour,
                "Detail": self._detail,
                "Black & White": self._bw,
                "Vintage": self._vintage,
                "Sketch": self._sketch,
            }.get(filter_name)
            if method:
                return method(image)
            return image
        except Exception as e:
            logger.error(f"Filter error ({filter_name}): {e}")
            return image

    def _blur(self, img):
        return img.filter(ImageFilter.BLUR)

    def _gaussian_blur(self, img):
        return img.filter(ImageFilter.GaussianBlur(radius=2))

    def _sharpen(self, img):
        return img.filter(ImageFilter.SHARPEN)

    def _edge_detection(self, img):
        return img.filter(ImageFilter.FIND_EDGES)

    def _emboss(self, img):
        return img.filter(ImageFilter.EMBOSS)

    def _smooth(self, img):
        return img.filter(ImageFilter.SMOOTH_MORE)

    def _contour(self, img):
        return img.filter(ImageFilter.CONTOUR)

    def _detail(self, img):
        return img.filter(ImageFilter.DETAIL)

    def _bw(self, img):
        return ImageOps.grayscale(img).convert("RGBA")

    def _vintage(self, img):
        rgb = img.convert("RGB")
        r, g, b = rgb.split()
        r = r.point(lambda i: min(255, i + 30))
        g = g.point(lambda i: max(0, i - 10))
        b = b.point(lambda i: max(0, i - 40))
        vintage = Image.merge("RGB", (r, g, b))
        enhanced = ImageEnhance.Contrast(vintage).enhance(0.85)
        return enhanced.convert("RGBA")

    def _sketch(self, img):
        cv_img = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2GRAY)
        inv = cv2.bitwise_not(cv_img)
        blurred = cv2.GaussianBlur(inv, (21, 21), 0)
        inv_blur = cv2.bitwise_not(blurred)
        sketch = cv2.divide(cv_img, inv_blur, scale=256.0)
        return Image.fromarray(sketch).convert("RGBA")
