import logging
import os
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime

logger = logging.getLogger(__name__)


class MetadataModule:
    def get_metadata(self, path) -> dict:
        info = {}
        try:
            stat = os.stat(path)
            info["File Name"] = os.path.basename(path)
            info["File Size"] = f"{stat.st_size / 1024:.1f} KB"
            info["Created"] = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M")
            info["Modified"] = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")

            with Image.open(path) as img:
                info["Width"] = f"{img.width} px"
                info["Height"] = f"{img.height} px"
                info["Format"] = img.format or "Unknown"
                info["Mode"] = img.mode
                try:
                    dpi = img.info.get("dpi", ("N/A", "N/A"))
                    info["DPI"] = f"{dpi[0]} x {dpi[1]}"
                except Exception:
                    info["DPI"] = "N/A"

                try:
                    exif_data = img._getexif()
                    if exif_data:
                        for tag_id, value in exif_data.items():
                            tag = TAGS.get(tag_id, tag_id)
                            if isinstance(value, bytes):
                                continue
                            info[f"EXIF: {tag}"] = str(value)[:80]
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Metadata error: {e}")
            info["Error"] = str(e)
        return info
