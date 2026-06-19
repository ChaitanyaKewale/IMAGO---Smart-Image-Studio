import logging
from PIL import Image, ImageDraw, ImageFont
import os

logger = logging.getLogger(__name__)

POSITIONS = ["Top Left", "Top Right", "Center", "Bottom Left", "Bottom Right"]


class WatermarkModule:
    def add_text(self, image: Image.Image, text, font_size=36, position="Bottom Right",
                 opacity=128, color=(255, 255, 255)) -> Image.Image:
        try:
            img = image.copy().convert("RGBA")
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except Exception:
                font = ImageFont.load_default()

            bbox = draw.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x, y = self._calc_position(img.size, tw, th, position)
            rgba_color = (*color, opacity)
            draw.text((x, y), text, font=font, fill=rgba_color)
            return Image.alpha_composite(img, overlay)
        except Exception as e:
            logger.error(f"Text watermark error: {e}")
            return image

    def add_image(self, image: Image.Image, logo_path, position="Bottom Right",
                  opacity=128, scale=0.2) -> Image.Image:
        try:
            img = image.copy().convert("RGBA")
            logo = Image.open(logo_path).convert("RGBA")
            new_w = int(img.width * scale)
            ratio = new_w / logo.width
            new_h = int(logo.height * ratio)
            logo = logo.resize((new_w, new_h), Image.LANCZOS)

            # Apply opacity
            r, g, b, a = logo.split()
            a = a.point(lambda p: int(p * opacity / 255))
            logo = Image.merge("RGBA", (r, g, b, a))

            x, y = self._calc_position(img.size, new_w, new_h, position)
            img.paste(logo, (x, y), logo)
            return img
        except Exception as e:
            logger.error(f"Image watermark error: {e}")
            return image

    def _calc_position(self, img_size, w, h, position):
        iw, ih = img_size
        pad = 20
        positions = {
            "Top Left": (pad, pad),
            "Top Right": (iw - w - pad, pad),
            "Center": ((iw - w) // 2, (ih - h) // 2),
            "Bottom Left": (pad, ih - h - pad),
            "Bottom Right": (iw - w - pad, ih - h - pad),
        }
        return positions.get(position, (pad, pad))
