"""Collect frames from the city traffic cameras, e.g. to label more bus/truck images for training."""
import time
from pathlib import Path

import cv2
import requests

from cameras import cameras
from utils.utils import get_cur_time, get_image

OUTPUT_DIR = Path("data/collected")
# The camera portal refreshes every camera image about every 15 seconds
REFRESH_SECONDS = 15

if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    while True:
        for camera in cameras:
            try:
                img = get_image(camera["id_camera"])
            except requests.RequestException as error:
                print(f"{camera['name']}: could not download image ({error})")
            else:
                file_name = f"{camera['id_camera']}_{get_cur_time()}.jpg"
                cv2.imwrite(str(OUTPUT_DIR / file_name), img)
                print(file_name)
            time.sleep(REFRESH_SECONDS / len(cameras))
