# IMAGO - Smart Image Studio 

A professional desktop image processing application built with Python.

---

## Features

- **Image Upload** — PNG, JPG, JPEG, WEBP, BMP, TIFF
- **Basic Operations** — Resize, Crop, Rotate, Flip, Aspect Lock
- **Enhancements** — Brightness, Contrast, Sharpness, Saturation, Color Balance (live preview)
- **Filters** — Blur, Gaussian Blur, Sharpen, Edge Detection, Emboss, Contour, B&W, Vintage, Sketch
- **Watermark** — Text + Image watermarks with opacity/position controls
- **OCR Text Extraction** — Extract, copy, save text from images (requires Tesseract)
- **Background Removal** — AI-powered via rembg (transparent/white/custom output)
- **Face Detection** — OpenCV Haar Cascade with bounding boxes & coordinates
- **Batch Processing** — Resize, convert, filter, watermark, or remove BG from multiple images
- **Metadata Viewer** — Width, height, DPI, format, EXIF data
- **Processing History** — SQLite-backed history with re-open support
- **Undo / Redo** — Full operation stack (30 levels)
- **Export** — PNG, JPG, WEBP, TIFF, BMP with quality control

---

## Requirements

- **Python 3.9+**
- **Tesseract OCR** (for OCR feature)

---

## Installation

### Step 1 — Clone / Extract the project

```bash
cd SmartImageStudio
```

### Step 2 — Create a virtual environment (recommended)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### Step 3 — Install Python dependencies

```bash
pip install -r requirements.txt
```

> **Note:** `rembg` may take a few minutes to install as it downloads AI model weights the first time you use it.

### Step 4 — Install Tesseract OCR

**Windows:**
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to: `C:\Program Files\Tesseract-OCR\`
3. (Optional) Add to system PATH

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install tesseract-ocr
```

### Step 5 — Run the application

```bash
python main.py
```

---

## Project Structure

```
SmartImageStudio/
├── main.py                      # Entry point
├── requirements.txt
├── README.md
│
├── gui/
│   └── app.py                   # Full GUI (sidebar, preview, panels, status bar)
│
├── core/
│   ├── image_processor.py       # Load, resize, crop, rotate, flip, undo/redo, save
│   ├── filters.py               # 11 image filters
│   ├── enhancements.py          # Brightness/contrast/sharpness/saturation/color
│   ├── watermark.py             # Text & image watermarks
│   ├── metadata.py              # File + EXIF metadata reader
│   ├── ocr.py                   # Tesseract OCR wrapper
│   ├── face_detection.py        # OpenCV Haar Cascade face detection
│   ├── background_removal.py    # rembg AI background removal
│   ├── batch_processor.py       # Multi-threaded batch operations
│   └── history_manager.py       # SQLite processing history
│
├── database/
│   └── history.db               # Auto-created SQLite database
│
├── assets/
│   ├── icons/
│   └── themes/
│
├── uploads/                     # Place source images here
├── outputs/                     # Processed images saved here
└── logs/
    └── app.log                  # Application log
```

---

## Keyboard Shortcuts

| Shortcut    | Action        |
|-------------|---------------|
| Ctrl+O      | Open image    |
| Ctrl+S      | Export image  |
| Ctrl+Z      | Undo          |
| Ctrl+Y      | Redo          |
| Mouse wheel | Zoom in/out   |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `pytesseract.pytesseract.TesseractNotFoundError` | Install Tesseract and ensure it's in PATH or at `C:\Program Files\Tesseract-OCR\tesseract.exe` |
| `rembg` slow first run | Normal — it downloads AI model weights (~170 MB) on first use |
| `customtkinter` not found | Run `pip install customtkinter` |
| Black screen / canvas empty | Resize the window or click "Fit" in the toolbar |

---

## Tech Stack

| Library | Purpose |
|---------|---------|
| CustomTkinter | Modern dark-themed GUI |
| Pillow (PIL) | Image loading, editing, enhancement |
| OpenCV | Face detection, sketch filter |
| pytesseract | OCR text extraction |
| rembg | AI background removal |
| SQLite3 | Processing history database |
| threading | Non-blocking heavy operations |

---

## Notes

- All operations are non-destructive — undo stack preserves 30 levels
- OCR is run in a background thread to prevent UI freezing
- Background removal, face detection, and batch processing all use threading
- Processed files are saved to `outputs/` by default
