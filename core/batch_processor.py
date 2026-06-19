import logging
import os
import threading
from PIL import Image
from core.filters import FiltersModule
from core.watermark import WatermarkModule
from core.background_removal import BackgroundRemovalModule

logger = logging.getLogger(__name__)


class BatchProcessor:
    def __init__(self, progress_callback=None, done_callback=None):
        self.progress_callback = progress_callback
        self.done_callback = done_callback
        self._stop = False
        self.filters = FiltersModule()
        self.watermark = WatermarkModule()
        self.bgremove = BackgroundRemovalModule()

    def stop(self):
        self._stop = True

    def process(self, file_paths, operation, output_dir, options=None):
        options = options or {}
        thread = threading.Thread(target=self._run, args=(file_paths, operation, output_dir, options), daemon=True)
        thread.start()

    def _run(self, file_paths, operation, output_dir, options):
        os.makedirs(output_dir, exist_ok=True)
        total = len(file_paths)
        results = []

        for i, path in enumerate(file_paths):
            if self._stop:
                break
            try:
                img = Image.open(path).convert("RGBA")
                out_name = os.path.splitext(os.path.basename(path))[0]

                if operation == "Resize":
                    w = int(options.get("width", 800))
                    h = int(options.get("height", 600))
                    img.thumbnail((w, h), Image.LANCZOS)
                    out_path = os.path.join(output_dir, f"{out_name}_resized.png")

                elif operation == "Convert Format":
                    fmt = options.get("format", "PNG").upper()
                    ext = fmt.lower()
                    out_path = os.path.join(output_dir, f"{out_name}.{ext}")
                    save_img = img.convert("RGB") if fmt in ("JPEG", "JPG", "BMP") else img
                    save_img.save(out_path, format=fmt.replace("JPG", "JPEG"))
                    results.append(out_path)
                    if self.progress_callback:
                        self.progress_callback(i + 1, total)
                    continue

                elif operation == "Apply Filter":
                    fname = options.get("filter", "Blur")
                    img = self.filters.apply(img, fname)
                    out_path = os.path.join(output_dir, f"{out_name}_{fname.replace(' ', '_')}.png")

                elif operation == "Add Watermark":
                    text = options.get("text", "Watermark")
                    img = self.watermark.add_text(img, text)
                    out_path = os.path.join(output_dir, f"{out_name}_watermarked.png")

                elif operation == "Remove Background":
                    img = self.bgremove.remove(img)
                    out_path = os.path.join(output_dir, f"{out_name}_nobg.png")
                else:
                    out_path = os.path.join(output_dir, f"{out_name}_processed.png")

                img.save(out_path, format="PNG")
                results.append(out_path)
            except Exception as e:
                logger.error(f"Batch error on {path}: {e}")

            if self.progress_callback:
                self.progress_callback(i + 1, total)

        if self.done_callback:
            self.done_callback(results)
