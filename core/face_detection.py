import logging
import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class FaceDetectionModule:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye.xml"
        )

    def detect(self, image: Image.Image):
        try:
            rgb = np.array(image.convert("RGB"))
            gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

            result_img = rgb.copy()
            face_list = []

            for i, (x, y, w, h) in enumerate(faces):
                cv2.rectangle(result_img, (x, y), (x + w, y + h), (0, 255, 80), 2)
                cv2.putText(result_img, f"Face {i+1}", (x, y - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 80), 2)
                face_list.append({"id": i + 1, "x": int(x), "y": int(y), "w": int(w), "h": int(h)})

            return Image.fromarray(result_img).convert("RGBA"), len(faces), face_list
        except Exception as e:
            logger.error(f"Face detection error: {e}")
            return image, 0, []
