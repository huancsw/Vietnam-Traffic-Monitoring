import io
import time

import cv2
import numpy as np
import requests
from PIL import Image

from utils.styles import CLASS_COLORS, COLOR_PRIMARY

CAMERA_URL = "https://giaothong.hochiminhcity.gov.vn/render/ImageHandler.ashx"
# The server stalls requests that do not look like a browser
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Referer": "https://giaothong.hochiminhcity.gov.vn/map.aspx",
}


def hex_to_bgr(color):
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))

    return b, g, r


def get_image(id_camera):
    """Download the latest frame of a traffic camera as a BGR numpy array."""
    response = requests.get(
        CAMERA_URL,
        params={"id": id_camera},
        headers=HEADERS,
        timeout=20,
    )
    response.raise_for_status()
    image = Image.open(io.BytesIO(response.content)).convert("RGB")

    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def draw_boxes(img, boxes, labels, probs, class_names):
    """Draw each detection with its class name and confidence on a BGR image (in place)."""
    for box, label, prob in zip(boxes, labels, probs):
        x1, y1, x2, y2 = (int(v) for v in box)
        color = hex_to_bgr(CLASS_COLORS.get(class_names[int(label)], COLOR_PRIMARY))
        text = f"{class_names[int(label)][:1].upper()} {float(prob) * 100:.0f}%"

        # Scale line and font with image size so boxes stay thin on any resolution
        scale = max(min(img.shape[:2]) / 720, 0.5)
        font_scale = 0.5 * scale
        pad = max(int(round(1.5 * scale)), 1)

        cv2.rectangle(img, (x1, y1), (x2, y2), color, 1, cv2.LINE_AA)
        (text_w, text_h), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)
        tag_w, tag_h = text_w + 2 * pad, text_h + baseline + 2 * pad
        top = y1 - tag_h if y1 - tag_h >= 0 else y1
        cv2.rectangle(img, (x1, top), (x1 + tag_w, top + tag_h), color, -1)
        cv2.putText(
            img, text, (x1 + pad, top + pad + text_h),
            cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), 1, cv2.LINE_AA,
        )

    return img


def get_cur_time():
    return time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())


def count_number_per_class(class_names, labels):
    """Count detections per class; every class appears in the result, even with 0."""
    counts = dict.fromkeys(class_names, 0)
    for label in labels:
        counts[class_names[int(label)]] += 1

    return counts
