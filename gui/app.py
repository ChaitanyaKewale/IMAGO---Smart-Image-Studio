import customtkinter as ctk
from tkinter import filedialog, messagebox, colorchooser
import tkinter as tk
from PIL import Image, ImageTk
import os
import threading
import logging

from core.image_processor import ImageProcessor
from core.filters import FiltersModule
from core.enhancements import EnhancementsModule
from core.watermark import WatermarkModule, POSITIONS
from core.metadata import MetadataModule
from core.ocr import OCRModule
from core.face_detection import FaceDetectionModule
from core.background_removal import BackgroundRemovalModule
from core.batch_processor import BatchProcessor
from core.history_manager import HistoryManager

logger = logging.getLogger(__name__)

SUPPORTED = [("Image Files", "*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.tif")]

# ── Color palette ──────────────────────────────────────────────────────────────
BG       = "#0F0F0F"
PANEL    = "#1E1E1E"
ACCENT   = "#2C2C2C"
TEXT     = "#FFFFFF"
SUBTEXT  = "#B0B0B0"
BTNBG    = "#333333"
BTNHOV   = "#444444"
GREEN    = "#4CAF50"
RED      = "#F44336"
BLUE     = "#2196F3"


class SmartImageStudio(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.title("Smart Image Studio")
        self.geometry("1400x860")
        self.minsize(1100, 700)
        self.configure(fg_color=BG)

        # Core modules
        self.processor = ImageProcessor()
        self.filters    = FiltersModule()
        self.enhance    = EnhancementsModule()
        self.watermark  = WatermarkModule()
        self.metadata   = MetadataModule()
        self.ocr        = OCRModule()
        self.face_det   = FaceDetectionModule()
        self.bg_remove  = BackgroundRemovalModule()
        self.history    = HistoryManager()

        self.current_tool   = None
        self._preview_image = None   # PhotoImage reference
        self._zoom          = 1.0
        self._drag_start    = None
        self._enhance_after = None
        self._before_photo  = None
        self._showing_before = False

        self._build_ui()
        self._bind_keys()

    # ── UI Construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_center()
        self._build_right_panel()
        self._build_status_bar()

    # ── Sidebar ────────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, fg_color=PANEL, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Logo / title
        title = ctk.CTkLabel(self.sidebar, text="⬛ Image Studio",
                             font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
                             text_color=TEXT)
        title.pack(pady=(18, 4), padx=16, anchor="w")
        ctk.CTkLabel(self.sidebar, text="Smart Processing Suite",
                     font=ctk.CTkFont(size=10), text_color=SUBTEXT).pack(anchor="w", padx=16)

        sep = ctk.CTkFrame(self.sidebar, height=1, fg_color=ACCENT)
        sep.pack(fill="x", padx=12, pady=12)

        tools = [
            ("📂", "Upload Image",      self._upload_image),
            ("⬛", "Recent Images",      lambda: self._activate("Recent Images")),
            ("⚙", "Basic Operations",   lambda: self._activate("Basic Operations")),
            ("✨", "Enhancements",       lambda: self._activate("Enhancements")),
            ("🎨", "Filters",            lambda: self._activate("Filters")),
            ("💧", "Watermark",          lambda: self._activate("Watermark")),
            ("🔍", "OCR Text",           lambda: self._activate("OCR Text")),
            ("✂", "Background Removal", lambda: self._activate("Background Removal")),
            ("👤", "Face Detection",     lambda: self._activate("Face Detection")),
            ("📦", "Batch Processing",   lambda: self._activate("Batch Processing")),
            ("📋", "Metadata",           lambda: self._activate("Metadata")),
            ("🕓", "History",            lambda: self._activate("History")),
        ]

        self._sidebar_btns = {}
        for icon, label, cmd in tools:
            btn = ctk.CTkButton(
                self.sidebar, text=f"  {icon}  {label}",
                anchor="w", height=36, corner_radius=6,
                fg_color="transparent", hover_color=ACCENT, text_color=TEXT,
                font=ctk.CTkFont(size=12),
                command=cmd
            )
            btn.pack(fill="x", padx=8, pady=2)
            self._sidebar_btns[label] = btn

        # Export button at bottom
        ctk.CTkFrame(self.sidebar, height=1, fg_color=ACCENT).pack(fill="x", padx=12, pady=12)
        ctk.CTkButton(self.sidebar, text="💾  Export Image", height=38,
                      fg_color=BTNBG, hover_color=BTNHOV, text_color=TEXT,
                      command=self._export_image).pack(fill="x", padx=12, pady=4)
        ctk.CTkButton(self.sidebar, text="↩ Undo", height=30, fg_color="transparent",
                      hover_color=ACCENT, text_color=SUBTEXT, command=self._undo).pack(fill="x", padx=12, pady=2)
        ctk.CTkButton(self.sidebar, text="↪ Redo", height=30, fg_color="transparent",
                      hover_color=ACCENT, text_color=SUBTEXT, command=self._redo).pack(fill="x", padx=12, pady=2)
        ctk.CTkButton(self.sidebar, text="⟳ Reset Original", height=30, fg_color="transparent",
                      hover_color=ACCENT, text_color=SUBTEXT, command=self._reset_image).pack(fill="x", padx=12, pady=2)

    # ── Center Preview ─────────────────────────────────────────────────────────

    def _build_center(self):
        self.center = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.center.grid(row=0, column=1, sticky="nsew")
        self.center.grid_rowconfigure(1, weight=1)
        self.center.grid_columnconfigure(0, weight=1)

        # Toolbar
        toolbar = ctk.CTkFrame(self.center, height=46, fg_color=PANEL, corner_radius=0)
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.grid_propagate(False)

        for text, cmd in [("🔍+", self._zoom_in), ("🔍-", self._zoom_out),
                          ("⊡ Fit", self._zoom_fit), ("⇄ Before/After", self._toggle_before)]:
            ctk.CTkButton(toolbar, text=text, width=90, height=30, fg_color=BTNBG,
                          hover_color=BTNHOV, text_color=TEXT, corner_radius=4,
                          command=cmd).pack(side="left", padx=4, pady=7)

        # Canvas
        canvas_frame = ctk.CTkFrame(self.center, fg_color="#141414", corner_radius=0)
        canvas_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(canvas_frame, bg="#141414", highlightthickness=0, cursor="crosshair")
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # Scrollbars
        vbar = tk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        vbar.grid(row=0, column=1, sticky="ns")
        hbar = tk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        hbar.grid(row=1, column=0, sticky="ew")
        self.canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)

        self.canvas.bind("<ButtonPress-1>",   self._on_drag_start)
        self.canvas.bind("<B1-Motion>",        self._on_drag)
        self.canvas.bind("<MouseWheel>",       self._on_scroll)
        self.canvas.bind("<Button-4>",         self._on_scroll)
        self.canvas.bind("<Button-5>",         self._on_scroll)

        self._draw_placeholder()

    def _draw_placeholder(self):
        self.canvas.delete("all")
        self.canvas.update_idletasks()
        cx = self.canvas.winfo_width() // 2 or 600
        cy = self.canvas.winfo_height() // 2 or 350
        self.canvas.create_text(cx, cy, text="📂  Upload an image to get started",
                                fill=SUBTEXT, font=("Segoe UI", 16))

    # ── Right Panel ────────────────────────────────────────────────────────────

    def _build_right_panel(self):
        self.right = ctk.CTkFrame(self, width=290, fg_color=PANEL, corner_radius=0)
        self.right.grid(row=0, column=2, sticky="nsew")
        self.right.grid_propagate(False)

        self.right_title = ctk.CTkLabel(self.right, text="Tool Settings",
                                        font=ctk.CTkFont(size=13, weight="bold"), text_color=TEXT)
        self.right_title.pack(pady=(16, 4), padx=14, anchor="w")
        ctk.CTkFrame(self.right, height=1, fg_color=ACCENT).pack(fill="x", padx=12, pady=6)

        self.right_content = ctk.CTkScrollableFrame(self.right, fg_color="transparent")
        self.right_content.pack(fill="both", expand=True, padx=6, pady=4)

        self._show_welcome_panel()

    def _clear_right(self):
        for w in self.right_content.winfo_children():
            w.destroy()

    def _show_welcome_panel(self):
        self._clear_right()
        msg = "Select a tool from the\nleft sidebar to begin."
        ctk.CTkLabel(self.right_content, text=msg, text_color=SUBTEXT,
                     font=ctk.CTkFont(size=12), justify="center").pack(pady=60)

    # ── Status Bar ─────────────────────────────────────────────────────────────

    def _build_status_bar(self):
        self.status_bar = ctk.CTkFrame(self, height=28, fg_color=ACCENT, corner_radius=0)
        self.status_bar.grid(row=1, column=0, columnspan=3, sticky="ew")

        self.status_res    = ctk.CTkLabel(self.status_bar, text="Resolution: —",  text_color=SUBTEXT, font=ctk.CTkFont(size=11))
        self.status_fmt    = ctk.CTkLabel(self.status_bar, text="Format: —",       text_color=SUBTEXT, font=ctk.CTkFont(size=11))
        self.status_size   = ctk.CTkLabel(self.status_bar, text="Size: —",         text_color=SUBTEXT, font=ctk.CTkFont(size=11))
        self.status_msg    = ctk.CTkLabel(self.status_bar, text="Ready",           text_color=GREEN,   font=ctk.CTkFont(size=11))

        for w in [self.status_res, self.status_fmt, self.status_size]:
            w.pack(side="left", padx=14, pady=4)
        self.status_msg.pack(side="right", padx=14, pady=4)

    def _update_status(self):
        if self.processor.current_image:
            w, h = self.processor.current_image.size
            self.status_res.configure(text=f"Resolution: {w} × {h}")
            fmt = "RGBA" if self.processor.current_image.mode == "RGBA" else self.processor.current_image.mode
            self.status_fmt.configure(text=f"Mode: {fmt}")
            if self.processor.current_path and os.path.exists(self.processor.current_path):
                sz = os.path.getsize(self.processor.current_path)
                self.status_size.configure(text=f"Size: {sz/1024:.1f} KB")

    def _set_status(self, msg, color=GREEN):
        self.status_msg.configure(text=msg, text_color=color)

    # ── Key Bindings ───────────────────────────────────────────────────────────

    def _bind_keys(self):
        self.bind("<Control-z>", lambda e: self._undo())
        self.bind("<Control-y>", lambda e: self._redo())
        self.bind("<Control-o>", lambda e: self._upload_image())
        self.bind("<Control-s>", lambda e: self._export_image())

    # ── Image Display ──────────────────────────────────────────────────────────

    def _display_image(self, img=None, zoom=None):
        if img is None:
            img = self.processor.current_image
        if img is None:
            return
        if zoom is not None:
            self._zoom = zoom

        self.canvas.update_idletasks()
        cw = self.canvas.winfo_width() or 800
        ch = self.canvas.winfo_height() or 600
        iw, ih = img.size

        display_w = int(iw * self._zoom)
        display_h = int(ih * self._zoom)

        resized = img.resize((max(1, display_w), max(1, display_h)), Image.LANCZOS)
        photo   = ImageTk.PhotoImage(resized)
        self._preview_image = photo

        self.canvas.delete("all")
        x = max(cw // 2, display_w // 2)
        y = max(ch // 2, display_h // 2)
        self.canvas.create_image(x, y, anchor="center", image=photo)
        self.canvas.configure(scrollregion=(0, 0, max(cw, display_w + 40), max(ch, display_h + 40)))
        self._update_status()

    def _zoom_in(self):
        self._zoom = min(self._zoom * 1.25, 8.0)
        self._display_image()

    def _zoom_out(self):
        self._zoom = max(self._zoom * 0.8, 0.05)
        self._display_image()

    def _zoom_fit(self):
        if not self.processor.current_image:
            return
        self.canvas.update_idletasks()
        cw = self.canvas.winfo_width() or 800
        ch = self.canvas.winfo_height() or 600
        iw, ih = self.processor.current_image.size
        self._zoom = min(cw / iw, ch / ih) * 0.9
        self._display_image()

    def _toggle_before(self):
        if not self.processor.original_image or not self.processor.current_image:
            return
        self._showing_before = not self._showing_before
        if self._showing_before:
            self._display_image(self.processor.original_image)
            self._set_status("Showing ORIGINAL", color=SUBTEXT)
        else:
            self._display_image(self.processor.current_image)
            self._set_status("Showing EDITED", color=GREEN)

    def _on_drag_start(self, e):
        self._drag_start = (e.x, e.y)

    def _on_drag(self, e):
        if self._drag_start:
            dx = e.x - self._drag_start[0]
            dy = e.y - self._drag_start[1]
            self.canvas.xview_scroll(-dx, "units")
            self.canvas.yview_scroll(-dy, "units")
            self._drag_start = (e.x, e.y)

    def _on_scroll(self, e):
        if e.num == 4 or e.delta > 0:
            self._zoom_in()
        else:
            self._zoom_out()

    # ── Tool Activation ────────────────────────────────────────────────────────

    def _activate(self, tool):
        # Highlight sidebar button
        for label, btn in self._sidebar_btns.items():
            btn.configure(fg_color=ACCENT if label == tool else "transparent")
        self.current_tool = tool
        self.right_title.configure(text=tool)
        self._clear_right()

        panels = {
            "Recent Images":      self._panel_recent,
            "Basic Operations":   self._panel_basic,
            "Enhancements":       self._panel_enhance,
            "Filters":            self._panel_filters,
            "Watermark":          self._panel_watermark,
            "OCR Text":           self._panel_ocr,
            "Background Removal": self._panel_bg_remove,
            "Face Detection":     self._panel_face,
            "Batch Processing":   self._panel_batch,
            "Metadata":           self._panel_metadata,
            "History":            self._panel_history,
        }
        fn = panels.get(tool)
        if fn:
            fn()

    # ── Upload ─────────────────────────────────────────────────────────────────

    def _upload_image(self):
        path = filedialog.askopenfilename(filetypes=SUPPORTED)
        if not path:
            return
        if self.processor.load_image(path):
            self._zoom = 1.0
            self.after(100, self._zoom_fit)
            self._set_status(f"Loaded: {os.path.basename(path)}")
            self.history.add_record(os.path.basename(path), "Open", "", path)
        else:
            messagebox.showerror("Error", "Failed to load image.")

    # ── Basic Operations Panel ─────────────────────────────────────────────────

    def _panel_basic(self):
        p = self.right_content
        self._label(p, "Resize")
        fr = ctk.CTkFrame(p, fg_color="transparent")
        fr.pack(fill="x", pady=2)
        self._wvar = tk.StringVar(value="800")
        self._hvar = tk.StringVar(value="600")
        ctk.CTkLabel(fr, text="W:", text_color=SUBTEXT, width=20).pack(side="left")
        ctk.CTkEntry(fr, textvariable=self._wvar, width=60).pack(side="left", padx=2)
        ctk.CTkLabel(fr, text="H:", text_color=SUBTEXT, width=20).pack(side="left")
        ctk.CTkEntry(fr, textvariable=self._hvar, width=60).pack(side="left", padx=2)

        self._lock_aspect = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(p, text="Lock Aspect Ratio", variable=self._lock_aspect,
                        text_color=SUBTEXT).pack(anchor="w", pady=2)
        self._btn(p, "Apply Resize", self._apply_resize)

        self._sep(p)
        self._label(p, "Rotate")
        self._rot_var = tk.StringVar(value="90")
        ctk.CTkOptionMenu(p, variable=self._rot_var,
                          values=["90", "180", "270", "-90"],
                          fg_color=BTNBG, button_color=ACCENT,
                          dropdown_fg_color=PANEL).pack(fill="x", pady=2)
        self._btn(p, "Apply Rotate", self._apply_rotate)

        self._sep(p)
        self._label(p, "Flip")
        row = ctk.CTkFrame(p, fg_color="transparent")
        row.pack(fill="x")
        self._btn(row, "↔ Horizontal", lambda: self._apply_flip("horizontal"), side="left", expand=True)
        self._btn(row, "↕ Vertical",   lambda: self._apply_flip("vertical"), side="left", expand=True)

        self._sep(p)
        self._label(p, "Crop  (px from edges)")
        cframe = ctk.CTkFrame(p, fg_color="transparent")
        cframe.pack(fill="x")
        self._crop_l = tk.StringVar(value="0")
        self._crop_t = tk.StringVar(value="0")
        self._crop_r = tk.StringVar(value="0")
        self._crop_b = tk.StringVar(value="0")
        for label, var in [("L", self._crop_l), ("T", self._crop_t), ("R", self._crop_r), ("B", self._crop_b)]:
            ctk.CTkLabel(cframe, text=f"{label}:", text_color=SUBTEXT, width=16).pack(side="left")
            ctk.CTkEntry(cframe, textvariable=var, width=44).pack(side="left", padx=1)
        self._btn(p, "Apply Crop", self._apply_crop)

    def _apply_resize(self):
        if not self._require_image(): return
        try:
            w, h = int(self._wvar.get()), int(self._hvar.get())
            self.processor.resize(w, h, keep_aspect=self._lock_aspect.get())
            self._display_image(); self._set_status("Resized")
        except ValueError:
            messagebox.showerror("Error", "Enter valid width and height.")

    def _apply_rotate(self):
        if not self._require_image(): return
        angle = int(self._rot_var.get())
        self.processor.rotate(angle); self._display_image(); self._set_status(f"Rotated {angle}°")

    def _apply_flip(self, direction):
        if not self._require_image(): return
        self.processor.flip(direction); self._display_image(); self._set_status(f"Flipped {direction}")

    def _apply_crop(self):
        if not self._require_image(): return
        try:
            iw, ih = self.processor.current_image.size
            l, t = int(self._crop_l.get()), int(self._crop_t.get())
            r, b = int(self._crop_r.get()), int(self._crop_b.get())
            self.processor.crop(l, t, iw - r, ih - b)
            self._display_image(); self._set_status("Cropped")
        except ValueError:
            messagebox.showerror("Error", "Enter valid crop values.")

    # ── Enhancements Panel ─────────────────────────────────────────────────────

    def _panel_enhance(self):
        p = self.right_content
        self._label(p, "Image Enhancements")
        ctk.CTkLabel(p, text="Sliders update live preview", text_color=SUBTEXT,
                     font=ctk.CTkFont(size=10)).pack(anchor="w")

        self._enh_vars = {}
        params = [
            ("Brightness",    0.0, 2.0, 1.0),
            ("Contrast",      0.0, 2.0, 1.0),
            ("Sharpness",     0.0, 3.0, 1.0),
            ("Saturation",    0.0, 2.0, 1.0),
            ("Color Balance", 0.0, 2.0, 1.0),
        ]
        for name, mn, mx, default in params:
            ctk.CTkLabel(p, text=name, text_color=SUBTEXT, font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(6, 0))
            var = tk.DoubleVar(value=default)
            val_label = ctk.CTkLabel(p, text=f"{default:.2f}", text_color=TEXT, font=ctk.CTkFont(size=11))
            val_label.pack(anchor="e")
            slider = ctk.CTkSlider(p, from_=mn, to=mx, variable=var, number_of_steps=40)
            slider.pack(fill="x", pady=2)

            def _on_change(v, vl=val_label, n=name):
                vl.configure(text=f"{float(v):.2f}")
                self._schedule_enhance()

            slider.configure(command=_on_change)
            self._enh_vars[name] = var

        self._sep(p)
        self._btn(p, "⟳ Reset Enhancements", self._reset_enhance)

    def _schedule_enhance(self):
        if self._enhance_after:
            self.after_cancel(self._enhance_after)
        self._enhance_after = self.after(250, self._apply_enhance_preview)

    def _apply_enhance_preview(self):
        if not self.processor.original_image:
            return
        ev = self._enh_vars
        img = self.enhance.apply(
            self.processor.original_image.copy(),
            brightness   = ev["Brightness"].get(),
            contrast     = ev["Contrast"].get(),
            sharpness    = ev["Sharpness"].get(),
            saturation   = ev["Saturation"].get(),
            color_balance= ev["Color Balance"].get(),
        )
        self.processor._push_undo()
        self.processor.current_image = img
        self._display_image()

    def _reset_enhance(self):
        for name, var in self._enh_vars.items():
            var.set(1.0)
        self._apply_enhance_preview()

    # ── Filters Panel ──────────────────────────────────────────────────────────

    def _panel_filters(self):
        p = self.right_content
        self._label(p, "Apply Filter")
        ctk.CTkLabel(p, text="Click any filter to apply", text_color=SUBTEXT,
                     font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(0, 6))

        for f in FiltersModule.FILTERS:
            self._btn(p, f, lambda fn=f: self._apply_filter(fn))

    def _apply_filter(self, name):
        if not self._require_image(): return
        self.processor._push_undo()
        self.processor.current_image = self.filters.apply(self.processor.current_image, name)
        self._display_image()
        self._set_status(f"Filter: {name}")

    # ── Watermark Panel ────────────────────────────────────────────────────────

    def _panel_watermark(self):
        p = self.right_content
        self._label(p, "Text Watermark")

        self._wm_text = tk.StringVar(value="© My Name")
        ctk.CTkEntry(p, textvariable=self._wm_text, placeholder_text="Watermark text").pack(fill="x", pady=2)

        ctk.CTkLabel(p, text="Font Size", text_color=SUBTEXT, font=ctk.CTkFont(size=11)).pack(anchor="w")
        self._wm_size = tk.IntVar(value=36)
        ctk.CTkSlider(p, from_=12, to=120, variable=self._wm_size, number_of_steps=20).pack(fill="x")

        ctk.CTkLabel(p, text="Position", text_color=SUBTEXT, font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(6, 0))
        self._wm_pos = tk.StringVar(value="Bottom Right")
        ctk.CTkOptionMenu(p, variable=self._wm_pos, values=POSITIONS,
                          fg_color=BTNBG, button_color=ACCENT, dropdown_fg_color=PANEL).pack(fill="x", pady=2)

        ctk.CTkLabel(p, text="Opacity  (0–255)", text_color=SUBTEXT, font=ctk.CTkFont(size=11)).pack(anchor="w")
        self._wm_opacity = tk.IntVar(value=160)
        ctk.CTkSlider(p, from_=10, to=255, variable=self._wm_opacity, number_of_steps=24).pack(fill="x")

        self._wm_color = [255, 255, 255]
        self._btn(p, "Pick Color", self._pick_wm_color)
        self._btn(p, "✓ Apply Text Watermark", self._apply_text_watermark)

        self._sep(p)
        self._label(p, "Image Watermark")
        self._wm_logo_path = tk.StringVar()
        ctk.CTkEntry(p, textvariable=self._wm_logo_path, placeholder_text="Logo path").pack(fill="x", pady=2)
        self._btn(p, "Browse Logo", self._browse_logo)

        ctk.CTkLabel(p, text="Opacity", text_color=SUBTEXT, font=ctk.CTkFont(size=11)).pack(anchor="w")
        self._wm_img_opacity = tk.IntVar(value=160)
        ctk.CTkSlider(p, from_=10, to=255, variable=self._wm_img_opacity, number_of_steps=24).pack(fill="x")

        ctk.CTkLabel(p, text="Scale", text_color=SUBTEXT, font=ctk.CTkFont(size=11)).pack(anchor="w")
        self._wm_scale = tk.DoubleVar(value=0.2)
        ctk.CTkSlider(p, from_=0.05, to=0.5, variable=self._wm_scale, number_of_steps=18).pack(fill="x")

        self._wm_img_pos = tk.StringVar(value="Bottom Right")
        ctk.CTkOptionMenu(p, variable=self._wm_img_pos, values=POSITIONS,
                          fg_color=BTNBG, button_color=ACCENT, dropdown_fg_color=PANEL).pack(fill="x", pady=2)
        self._btn(p, "✓ Apply Image Watermark", self._apply_image_watermark)

    def _pick_wm_color(self):
        color = colorchooser.askcolor(title="Watermark Color", color="#ffffff")
        if color[0]:
            self._wm_color = [int(c) for c in color[0]]

    def _browse_logo(self):
        path = filedialog.askopenfilename(filetypes=[("Image", "*.png *.jpg *.jpeg *.webp")])
        if path:
            self._wm_logo_path.set(path)

    def _apply_text_watermark(self):
        if not self._require_image(): return
        self.processor._push_undo()
        self.processor.current_image = self.watermark.add_text(
            self.processor.current_image,
            self._wm_text.get(),
            font_size=self._wm_size.get(),
            position=self._wm_pos.get(),
            opacity=self._wm_opacity.get(),
            color=tuple(self._wm_color)
        )
        self._display_image(); self._set_status("Text watermark applied")

    def _apply_image_watermark(self):
        if not self._require_image(): return
        logo = self._wm_logo_path.get()
        if not logo or not os.path.exists(logo):
            messagebox.showerror("Error", "Select a valid logo image.")
            return
        self.processor._push_undo()
        self.processor.current_image = self.watermark.add_image(
            self.processor.current_image, logo,
            position=self._wm_img_pos.get(),
            opacity=self._wm_img_opacity.get(),
            scale=self._wm_scale.get()
        )
        self._display_image(); self._set_status("Image watermark applied")

    # ── OCR Panel ──────────────────────────────────────────────────────────────

    def _panel_ocr(self):
        p = self.right_content
        self._label(p, "OCR Text Extraction")
        ctk.CTkLabel(p, text="Requires Tesseract-OCR installed", text_color=SUBTEXT,
                     font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(0, 6))
        self._btn(p, "▶ Extract Text", self._run_ocr)
        self._sep(p)
        self._ocr_text = ctk.CTkTextbox(p, height=260, fg_color=ACCENT, text_color=TEXT,
                                         font=ctk.CTkFont(size=11))
        self._ocr_text.pack(fill="x", pady=4)
        row = ctk.CTkFrame(p, fg_color="transparent")
        row.pack(fill="x")
        self._btn(row, "Copy", self._copy_ocr, side="left", expand=True)
        self._btn(row, "Save TXT", self._save_ocr, side="left", expand=True)

    def _run_ocr(self):
        if not self._require_image(): return
        self._set_status("Running OCR…", color=BLUE)
        img = self.processor.current_image.copy()
        def _task():
            text = self.ocr.extract_text(img)
            self.after(0, lambda: self._ocr_done(text))
        threading.Thread(target=_task, daemon=True).start()

    def _ocr_done(self, text):
        self._ocr_text.delete("1.0", "end")
        self._ocr_text.insert("1.0", text)
        self._set_status("OCR complete")

    def _copy_ocr(self):
        text = self._ocr_text.get("1.0", "end").strip()
        self.clipboard_clear(); self.clipboard_append(text)
        self._set_status("Copied to clipboard")

    def _save_ocr(self):
        text = self._ocr_text.get("1.0", "end").strip()
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("Text File", "*.txt")])
        if path:
            self.ocr.save_text(text, path)
            self._set_status("OCR saved")

    # ── Background Removal Panel ───────────────────────────────────────────────

    def _panel_bg_remove(self):
        p = self.right_content
        self._label(p, "Background Removal")
        ctk.CTkLabel(p, text="Uses rembg AI model", text_color=SUBTEXT,
                     font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(0, 6))

        self._bg_mode = tk.StringVar(value="Transparent")
        ctk.CTkOptionMenu(p, variable=self._bg_mode,
                          values=["Transparent", "White", "Custom Color"],
                          fg_color=BTNBG, button_color=ACCENT, dropdown_fg_color=PANEL).pack(fill="x", pady=4)

        self._bg_custom_color = (255, 255, 255)
        self._btn(p, "Pick Custom Color", self._pick_bg_color)
        self._sep(p)
        self._btn(p, "▶ Remove Background", self._run_bg_remove, color=RED)

    def _pick_bg_color(self):
        color = colorchooser.askcolor(title="Background Color")
        if color[0]:
            self._bg_custom_color = tuple(int(c) for c in color[0])

    def _run_bg_remove(self):
        if not self._require_image(): return
        self._set_status("Removing background…", color=BLUE)
        img  = self.processor.current_image.copy()
        mode = self._bg_mode.get()
        if mode == "Transparent":
            bg_color = None
        elif mode == "White":
            bg_color = (255, 255, 255)
        else:
            bg_color = self._bg_custom_color

        def _task():
            result = self.bg_remove.remove(img, bg_color=bg_color)
            self.after(0, lambda: self._bg_done(result))
        threading.Thread(target=_task, daemon=True).start()

    def _bg_done(self, result):
        self.processor._push_undo()
        self.processor.current_image = result
        self._display_image()
        self._set_status("Background removed")
        if self.processor.current_path:
            self.history.add_record(os.path.basename(self.processor.current_path), "Background Removal")

    # ── Face Detection Panel ───────────────────────────────────────────────────

    def _panel_face(self):
        p = self.right_content
        self._label(p, "Face Detection")
        ctk.CTkLabel(p, text="Using OpenCV Haar Cascade", text_color=SUBTEXT,
                     font=ctk.CTkFont(size=10)).pack(anchor="w", pady=(0, 6))
        self._btn(p, "▶ Detect Faces", self._run_face_detect)
        self._sep(p)
        self._face_info = ctk.CTkTextbox(p, height=180, fg_color=ACCENT,
                                          text_color=TEXT, font=ctk.CTkFont(size=11))
        self._face_info.pack(fill="x", pady=4)

    def _run_face_detect(self):
        if not self._require_image(): return
        self._set_status("Detecting faces…", color=BLUE)
        img = self.processor.current_image.copy()
        def _task():
            result, count, face_list = self.face_det.detect(img)
            self.after(0, lambda: self._face_done(result, count, face_list))
        threading.Thread(target=_task, daemon=True).start()

    def _face_done(self, result, count, face_list):
        self.processor._push_undo()
        self.processor.current_image = result
        self._display_image()
        info = f"Faces detected: {count}\n\n"
        for f in face_list:
            info += f"Face {f['id']}: x={f['x']}, y={f['y']}, {f['w']}×{f['h']}px\n"
        self._face_info.delete("1.0", "end")
        self._face_info.insert("1.0", info)
        self._set_status(f"{count} face(s) detected")

    # ── Batch Processing Panel ─────────────────────────────────────────────────

    def _panel_batch(self):
        p = self.right_content
        self._label(p, "Batch Processing")
        self._batch_files = []
        self._btn(p, "Select Images", self._select_batch_files)
        self._batch_count = ctk.CTkLabel(p, text="No files selected", text_color=SUBTEXT,
                                          font=ctk.CTkFont(size=11))
        self._batch_count.pack(anchor="w", pady=2)

        ctk.CTkLabel(p, text="Operation", text_color=SUBTEXT, font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(6, 0))
        self._batch_op = tk.StringVar(value="Resize")
        ctk.CTkOptionMenu(p, variable=self._batch_op,
                          values=["Resize", "Convert Format", "Apply Filter", "Add Watermark", "Remove Background"],
                          fg_color=BTNBG, button_color=ACCENT,
                          dropdown_fg_color=PANEL, command=self._batch_op_changed).pack(fill="x", pady=2)

        self._batch_opt_frame = ctk.CTkFrame(p, fg_color="transparent")
        self._batch_opt_frame.pack(fill="x", pady=4)
        self._build_batch_opts()

        self._btn(p, "Select Output Folder", self._select_batch_out)
        self._batch_out_label = ctk.CTkLabel(p, text="outputs/", text_color=SUBTEXT,
                                              font=ctk.CTkFont(size=10), wraplength=240)
        self._batch_out_label.pack(anchor="w")
        self._batch_out_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")

        self._sep(p)
        self._batch_progress = ctk.CTkProgressBar(p)
        self._batch_progress.pack(fill="x", pady=4)
        self._batch_progress.set(0)
        self._btn(p, "▶ Start Batch", self._run_batch, color=GREEN)

    def _select_batch_files(self):
        files = filedialog.askopenfilenames(filetypes=SUPPORTED)
        if files:
            self._batch_files = list(files)
            self._batch_count.configure(text=f"{len(files)} image(s) selected")

    def _select_batch_out(self):
        path = filedialog.askdirectory()
        if path:
            self._batch_out_path = path
            self._batch_out_label.configure(text=path)

    def _batch_op_changed(self, val=None):
        for w in self._batch_opt_frame.winfo_children():
            w.destroy()
        self._build_batch_opts()

    def _build_batch_opts(self):
        op = self._batch_op.get()
        f  = self._batch_opt_frame
        if op == "Resize":
            self._b_w = tk.StringVar(value="800")
            self._b_h = tk.StringVar(value="600")
            row = ctk.CTkFrame(f, fg_color="transparent"); row.pack(fill="x")
            ctk.CTkLabel(row, text="W:", text_color=SUBTEXT, width=18).pack(side="left")
            ctk.CTkEntry(row, textvariable=self._b_w, width=60).pack(side="left", padx=2)
            ctk.CTkLabel(row, text="H:", text_color=SUBTEXT, width=18).pack(side="left")
            ctk.CTkEntry(row, textvariable=self._b_h, width=60).pack(side="left", padx=2)
        elif op == "Convert Format":
            self._b_fmt = tk.StringVar(value="PNG")
            ctk.CTkOptionMenu(f, variable=self._b_fmt, values=["PNG", "JPEG", "WEBP", "BMP", "TIFF"],
                              fg_color=BTNBG, button_color=ACCENT, dropdown_fg_color=PANEL).pack(fill="x")
        elif op == "Apply Filter":
            self._b_filter = tk.StringVar(value="Blur")
            ctk.CTkOptionMenu(f, variable=self._b_filter, values=FiltersModule.FILTERS,
                              fg_color=BTNBG, button_color=ACCENT, dropdown_fg_color=PANEL).pack(fill="x")
        elif op == "Add Watermark":
            self._b_wm_text = tk.StringVar(value="© Watermark")
            ctk.CTkEntry(f, textvariable=self._b_wm_text, placeholder_text="Watermark text").pack(fill="x")

    def _run_batch(self):
        if not self._batch_files:
            messagebox.showwarning("No Files", "Select images first."); return
        op      = self._batch_op.get()
        options = {}
        if op == "Resize":
            options = {"width": self._b_w.get(), "height": self._b_h.get()}
        elif op == "Convert Format":
            options = {"format": self._b_fmt.get()}
        elif op == "Apply Filter":
            options = {"filter": self._b_filter.get()}
        elif op == "Add Watermark":
            options = {"text": self._b_wm_text.get()}

        total = len(self._batch_files)
        self._batch_progress.set(0)

        def _prog(done, t):
            self.after(0, lambda: self._batch_progress.set(done / t))

        def _done(results):
            self.after(0, lambda: (self._set_status(f"Batch done — {len(results)} files"), self._batch_progress.set(1.0)))

        bp = BatchProcessor(progress_callback=_prog, done_callback=_done)
        bp.process(self._batch_files, op, self._batch_out_path, options)
        self._set_status("Batch running…", color=BLUE)

    # ── Metadata Panel ─────────────────────────────────────────────────────────

    def _panel_metadata(self):
        p = self.right_content
        self._label(p, "Image Metadata")
        if not self.processor.current_path:
            ctk.CTkLabel(p, text="Load an image first.", text_color=SUBTEXT).pack(pady=20)
            return
        data = self.metadata.get_metadata(self.processor.current_path)
        for key, val in data.items():
            row = ctk.CTkFrame(p, fg_color=ACCENT, corner_radius=4)
            row.pack(fill="x", pady=2, padx=2)
            ctk.CTkLabel(row, text=key, text_color=SUBTEXT,
                         font=ctk.CTkFont(size=10), width=120, anchor="w").pack(side="left", padx=6, pady=3)
            ctk.CTkLabel(row, text=val, text_color=TEXT,
                         font=ctk.CTkFont(size=10), anchor="w", wraplength=130).pack(side="left", padx=4)

    # ── History Panel ──────────────────────────────────────────────────────────

    def _panel_history(self):
        p = self.right_content
        self._label(p, "Processing History")
        records = self.history.get_all()
        if not records:
            ctk.CTkLabel(p, text="No history yet.", text_color=SUBTEXT).pack(pady=20)
        for rec in records:
            _, fname, date, op, out_path = rec
            row = ctk.CTkFrame(p, fg_color=ACCENT, corner_radius=5)
            row.pack(fill="x", pady=3, padx=2)
            ctk.CTkLabel(row, text=fname, text_color=TEXT, font=ctk.CTkFont(size=11, weight="bold"),
                         anchor="w").pack(anchor="w", padx=8, pady=(4, 0))
            ctk.CTkLabel(row, text=f"{op}  •  {date}", text_color=SUBTEXT,
                         font=ctk.CTkFont(size=10), anchor="w").pack(anchor="w", padx=8)
            if out_path and os.path.exists(out_path):
                ctk.CTkButton(row, text="Open", width=50, height=22, fg_color=BTNBG,
                              hover_color=BTNHOV, text_color=TEXT,
                              command=lambda pp=out_path: self._reopen_file(pp)).pack(anchor="e", padx=8, pady=4)

        self._sep(p)
        self._btn(p, "Clear History", self._clear_history, color=RED)

    def _reopen_file(self, path):
        if self.processor.load_image(path):
            self.after(100, self._zoom_fit)
            self._set_status(f"Reopened: {os.path.basename(path)}")

    def _clear_history(self):
        self.history.clear_history()
        self._panel_history()

    # ── Recent Images Panel ────────────────────────────────────────────────────

    def _panel_recent(self):
        p = self.right_content
        self._label(p, "Recent Files")
        records = self.history.get_all()
        seen = set()
        for rec in records:
            _, fname, date, op, out_path = rec
            in_path = out_path
            if in_path in seen:
                continue
            seen.add(in_path)
            row = ctk.CTkFrame(p, fg_color=ACCENT, corner_radius=5)
            row.pack(fill="x", pady=3, padx=2)
            ctk.CTkLabel(row, text=fname, text_color=TEXT, font=ctk.CTkFont(size=11),
                         anchor="w").pack(anchor="w", padx=8, pady=(4, 0))
            ctk.CTkLabel(row, text=date, text_color=SUBTEXT, font=ctk.CTkFont(size=10),
                         anchor="w").pack(anchor="w", padx=8)
            if in_path and os.path.exists(in_path):
                ctk.CTkButton(row, text="Open", width=50, height=22,
                              fg_color=BTNBG, hover_color=BTNHOV, text_color=TEXT,
                              command=lambda pp=in_path: self._reopen_file(pp)).pack(anchor="e", padx=8, pady=4)
        if not seen:
            ctk.CTkLabel(p, text="No recent files.", text_color=SUBTEXT).pack(pady=20)

    # ── Export ─────────────────────────────────────────────────────────────────

    def _export_image(self):
        if not self._require_image(): return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("WEBP", "*.webp"),
                       ("TIFF", "*.tiff"), ("BMP", "*.bmp")]
        )
        if path:
            quality = 95
            if self.processor.save(path, quality=quality):
                self._set_status(f"Saved: {os.path.basename(path)}")
                self.history.add_record(os.path.basename(path), "Export", path,
                                        self.processor.current_path or "")
            else:
                messagebox.showerror("Error", "Failed to save image.")

    # ── Undo / Redo / Reset ────────────────────────────────────────────────────

    def _undo(self):
        if self.processor.undo():
            self._display_image(); self._set_status("Undone")

    def _redo(self):
        if self.processor.redo():
            self._display_image(); self._set_status("Redone")

    def _reset_image(self):
        if self.processor.reset_to_original():
            self._display_image(); self._set_status("Reset to original")

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _require_image(self):
        if not self.processor.current_image:
            messagebox.showwarning("No Image", "Please upload an image first.")
            return False
        return True

    def _label(self, parent, text):
        ctk.CTkLabel(parent, text=text, text_color=TEXT,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(8, 2))

    def _sep(self, parent):
        ctk.CTkFrame(parent, height=1, fg_color=ACCENT).pack(fill="x", pady=8)

    def _btn(self, parent, text, cmd, color=None, side=None, expand=False):
        kwargs = dict(
            text=text, height=32, corner_radius=5,
            fg_color=color or BTNBG, hover_color=BTNHOV,
            text_color=TEXT, font=ctk.CTkFont(size=12),
            command=cmd
        )
        btn = ctk.CTkButton(parent, **kwargs)
        if side:
            btn.pack(side=side, fill="x", expand=expand, padx=2, pady=2)
        else:
            btn.pack(fill="x", pady=2)
        return btn
