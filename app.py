import tempfile
import time
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import requests
import streamlit as st
from PIL import Image

from cameras import cameras
from utils.styles import APP_CSS, CLASS_COLORS, badges_html, counter_html, feature_html, header_html
from utils.utils import count_number_per_class, draw_boxes, get_image
from yolo_predictor import YoloPredictor

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "yolo26n.pt"
SAMPLE_RESULT_PATH = BASE_DIR / "assets" / "sample_result.jpg"
LOGO_PATH = BASE_DIR / "assets" / "hcmute_logo.png"
BANNER_PATH = BASE_DIR / "assets" / "banner_feathered.png"
OUTPUT_VIDEO = BASE_DIR / "outputs" / "output.avi"
# The camera portal refreshes every camera image about every 15 seconds
CAMERA_REFRESH_SECONDS = 15

st.set_page_config(page_title="Vietnam Traffic Monitoring", page_icon="\U0001F697", layout="wide")


@st.cache_resource
def load_model(model_path):
    return YoloPredictor(model_path)


def detect(img, model, threshold):
    """Run detection on a BGR image; returns the annotated image and the per-class counts."""
    boxes, labels, probs = model.predict(img, prob_threshold=threshold)
    annotated = draw_boxes(img, boxes, labels, probs, model.class_names)

    return annotated, count_number_per_class(model.class_names, labels)


def to_display_image(img, width=1000):
    """Convert a BGR image to RGB and resize it to `width` pixels wide."""
    h, w, _ = img.shape
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    return cv2.resize(img, (width, int(width * h / w)))


def create_counters(class_names):
    """Show one counter card per class; returns the card placeholders by class name."""
    counters = {}
    for column, name in zip(st.columns(len(class_names)), class_names):
        counters[name] = column.empty()
        counters[name].markdown(counter_html(name, 0), unsafe_allow_html=True)

    return counters


def update_counters(counters, counts):
    for name, placeholder in counters.items():
        placeholder.markdown(counter_html(name, counts[name]), unsafe_allow_html=True)


def process_video(uploaded_video, model, threshold, record, counters, space_img, download_slot):
    """Detect vehicles frame by frame, optionally saving the annotated video for download."""
    with tempfile.NamedTemporaryFile(suffix=Path(uploaded_video.name).suffix, delete=False) as temp_file:
        temp_file.write(uploaded_video.read())
    vid = cv2.VideoCapture(temp_file.name)
    fps = vid.get(cv2.CAP_PROP_FPS) or 20.0

    out_video = None
    if record:
        OUTPUT_VIDEO.parent.mkdir(exist_ok=True)
        width = int(vid.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
        out_video = cv2.VideoWriter(str(OUTPUT_VIDEO), cv2.VideoWriter_fourcc(*"XVID"), fps, (width, height))

    try:
        start = time.time()
        frame_index = 0
        while vid.grab():
            frame_index += 1
            # Drop frames when detection is slower than the video so playback stays real time
            if not record and time.time() - start > frame_index / fps:
                continue

            ret, frame = vid.retrieve()
            if not ret:
                break

            img_pred, counts = detect(frame, model, threshold)
            update_counters(counters, counts)
            if out_video is not None:
                out_video.write(img_pred)
            space_img.image(to_display_image(img_pred), width="stretch")
    finally:
        vid.release()
        if out_video is not None:
            out_video.release()
        Path(temp_file.name).unlink(missing_ok=True)

    if record:
        with open(OUTPUT_VIDEO, "rb") as f:
            download_slot.download_button("Download annotated video", f, "output.avi", mime="video/x-msvideo")


def render_about(model):
    with st.container(border=True):
        st.markdown(
            "Detect vehicles (" + ", ".join(model.class_names) + ") in images, videos and live traffic "
            "cameras in Vietnam, and follow the vehicle counts in real time. Live camera images come from the "
            "[Ho Chi Minh City Traffic Information Portal](http://giaothong.hochiminhcity.gov.vn)."
        )
        if SAMPLE_RESULT_PATH.exists():
            st.image(str(SAMPLE_RESULT_PATH), caption="Example detection result", width=640)

    st.markdown("<div class='card-title' style='margin-top:8px'>Features</div>", unsafe_allow_html=True)
    for column, (title, text) in zip(
        st.columns(3),
        (
            ("Run on Image", "Upload an image and count the vehicles in it."),
            ("Run on Video", "Count vehicles frame by frame and optionally record the annotated video."),
            (
                "Run on Live Camera",
                f"Pick a traffic camera, count vehicles every {CAMERA_REFRESH_SECONDS} seconds "
                "and follow the counts on a chart.",
            ),
        ),
    ):
        column.markdown(feature_html(title, text), unsafe_allow_html=True)
    st.markdown("<div class='footer'>Built with Streamlit and YOLO26n</div>", unsafe_allow_html=True)


def render_sidebar(model):
    """Mode and detection settings; returns the selected mode and confidence threshold."""
    with st.sidebar:
        st.markdown("<div class='side-title'>Mode</div>", unsafe_allow_html=True)
        app_mode = st.radio(
            "Mode",
            ("About Page", "Run on Image", "Run on Live Camera", "Run on Video"),
            label_visibility="collapsed",
        )
        threshold = None
        if app_mode != "About Page":
            st.markdown("<div class='side-title'>Detection</div>", unsafe_allow_html=True)
            threshold = st.slider("Detection Confidence", min_value=1, max_value=99, value=50) / 100

        st.divider()
        st.markdown("<div class='side-title'>About</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='side-text'>Vehicle detection and counting on Vietnamese street scenes.</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='side-title' style='margin-top:12px'>Tech</div>", unsafe_allow_html=True)
        st.markdown(badges_html(("Python", "YOLO26n", "Ultralytics", "OpenCV", "Streamlit")), unsafe_allow_html=True)

    return app_mode, threshold


def UI(model):
    st.markdown(APP_CSS, unsafe_allow_html=True)
    st.markdown(
        header_html(
            "Vietnam Traffic Monitoring",
            "Detect and count vehicles in images, videos and live traffic cameras.",
            LOGO_PATH,
            BANNER_PATH,
        ),
        unsafe_allow_html=True,
    )
    app_mode, threshold = render_sidebar(model)

    if app_mode == "About Page":
        render_about(model)
        return

    counters = create_counters(model.class_names)

    if app_mode == "Run on Image":
        uploaded_image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

        with st.container(border=True):
            space_img = st.empty()
        if uploaded_image is not None:
            img = cv2.cvtColor(np.array(Image.open(uploaded_image).convert("RGB")), cv2.COLOR_RGB2BGR)
            img_pred, counts = detect(img, model, threshold)
            update_counters(counters, counts)
            space_img.image(to_display_image(img_pred), width="stretch")

    elif app_mode == "Run on Live Camera":
        id_cameras = [{"name": "Choose camera", "id_camera": ""}] + cameras
        camera_names = [camera["name"] for camera in id_cameras]
        selected_camera = st.selectbox("Id Camera", camera_names)
        id_camera = id_cameras[camera_names.index(selected_camera)]["id_camera"]

        b21, b22 = st.columns((3, 2))
        with b21.container(border=True):
            space_img = st.empty()
        with b22.container(border=True):
            st.markdown("<div class='card-title'>Vehicle counts</div>", unsafe_allow_html=True)
            history = pd.DataFrame([[0] * len(model.class_names)] * 20, columns=model.class_names)
            chart_colors = [CLASS_COLORS.get(name, "#1976D2") for name in model.class_names]
            space_graph = st.line_chart(history, height=520, color=chart_colors)
        if id_camera != "":
            while True:
                try:
                    img = get_image(id_camera)
                except requests.RequestException as error:
                    b21.error(
                        "Không thể tải ảnh từ camera giao thông. "
                        f"Máy chủ camera không phản hồi: {error}"
                    )
                    break

                img_pred, counts = detect(img, model, threshold)
                update_counters(counters, counts)
                space_img.image(to_display_image(img_pred), width="stretch")

                history = pd.concat([history.iloc[1:], pd.DataFrame([counts])], ignore_index=True)
                space_graph.line_chart(history, height=520, color=chart_colors)
                time.sleep(CAMERA_REFRESH_SECONDS)

    elif app_mode == "Run on Video":
        b21, b22 = st.columns((3, 1))
        uploaded_video = b21.file_uploader("Upload a video", type=["mp4", "mov", "avi"])
        record = b22.checkbox("Record Video")
        download_slot = b22.container()

        with st.container(border=True):
            space_img = st.empty()
        if uploaded_video:
            process_video(uploaded_video, model, threshold, record, counters, space_img, download_slot)


if __name__ == "__main__":
    UI(load_model(str(MODEL_PATH)))
