"""Theme (navy/blue, white cards) and HTML snippets for the Streamlit app."""

import base64
from html import escape
from pathlib import Path

COLOR_NAVY = "#123B7A"
COLOR_PRIMARY = "#1976D2"
COLOR_BG = "#F3F7FC"
COLOR_CARD = "#FFFFFF"
COLOR_BORDER = "#DDE7F3"
COLOR_TEXT = "#172E52"
COLOR_MUTED = "#59708F"

# One accent color per vehicle class
CLASS_COLORS = {
    "car": "#1976D2",
    "motorbike": "#10B981",
    "bus": "#F59E0B",
    "truck": "#EF4444",
}

APP_CSS = f"""
<style>
html {{ font-size: 125%; }}
html, body, [class*="css"] {{
    font-family: "Segoe UI", "Segoe UI Variable Display", Arial, sans-serif;
}}
#MainMenu, footer, header[data-testid="stHeader"] {{ visibility: hidden; height: 0; }}
.block-container {{ padding: 1.2rem 2rem 2rem 2rem; max-width: 100%; }}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background-color: {COLOR_CARD};
    border-right: 1px solid {COLOR_BORDER};
}}
section[data-testid="stSidebar"] .block-container {{ padding-top: 1.2rem; }}
.side-title {{
    font-size: 19px; font-weight: 700; color: {COLOR_NAVY};
    margin: 5px 0 8px 0;
}}
.side-text {{ font-size: 15.5px; color: {COLOR_MUTED}; line-height: 1.5; }}
.badges {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }}
.badge {{
    background: #EFF6FF; color: {COLOR_PRIMARY}; border: 1px solid #BFDBFE;
    border-radius: 15px; padding: 3px 12px; font-size: 15px; font-weight: 600;
}}

/* Header banner */
.app-header {{
    position: relative; overflow: hidden;
    display: flex; align-items: center; gap: 22px;
    padding: 20px 30px; margin-bottom: 20px;
    background-color: {COLOR_CARD};
    border: 1px solid {COLOR_BORDER}; border-radius: 14px;
    box-shadow: 0 2px 10px rgba(18, 59, 122, 0.06);
}}
.app-header .banner {{
    position: absolute; top: 0; right: 0; height: 100%; width: 60%;
    background-size: cover; background-position: right center;
    opacity: 0.9; pointer-events: none;
}}
.app-header img.logo {{ height: 90px; position: relative; }}
.app-header .texts {{ position: relative; }}
.app-header h1 {{
    margin: 0; padding: 0; font-size: 35px; font-weight: 800;
    color: {COLOR_NAVY}; letter-spacing: 0.2px;
}}
.app-header .sub {{ margin-top: 5px; font-size: 17.5px; font-weight: 500; color: {COLOR_MUTED}; }}
.app-header .accent {{
    width: 70px; height: 5px; border-radius: 3px; margin-top: 10px;
    background: {COLOR_PRIMARY};
}}

/* Counter cards */
.counter {{
    background: {COLOR_CARD}; border: 1px solid {COLOR_BORDER}; border-radius: 14px;
    padding: 15px 20px; border-left-width: 6px;
    box-shadow: 0 1px 6px rgba(18, 59, 122, 0.05);
}}
.counter .name {{
    font-size: 15px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.75px; color: {COLOR_MUTED};
}}
.counter .value {{ font-size: 40px; font-weight: 800; line-height: 1.15; }}

/* Cards: bordered containers, images, charts */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {COLOR_CARD}; border-color: {COLOR_BORDER} !important; border-radius: 14px;
}}
div[data-testid="stImage"] img {{ border-radius: 10px; }}
.card-title {{ font-size: 19px; font-weight: 700; color: {COLOR_NAVY}; margin-bottom: 5px; }}

/* Widgets */
div[data-baseweb="select"] > div, div[data-testid="stFileUploader"] section {{
    border-radius: 10px; border-color: {COLOR_BORDER};
}}
div[data-testid="stFileUploader"] section {{ background: #F8FAFC; border: 1.5px dashed #BFD3EA; }}
.stButton > button, .stDownloadButton > button {{
    background: {COLOR_PRIMARY}; color: #fff; border: none; border-radius: 10px;
    padding: 0.45rem 1.2rem; font-weight: 600;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{ background: {COLOR_NAVY}; color: #fff; }}

/* About page */
.feature {{
    background: {COLOR_CARD}; border: 1px solid {COLOR_BORDER}; border-radius: 14px;
    padding: 20px 22px; height: 100%;
    box-shadow: 0 1px 6px rgba(18, 59, 122, 0.05);
}}
.feature h4 {{ margin: 0 0 8px 0; color: {COLOR_NAVY}; font-size: 20px; }}
.feature p {{ margin: 0; color: {COLOR_MUTED}; font-size: 17px; line-height: 1.5; }}
.footer {{ text-align: center; color: {COLOR_MUTED}; font-size: 15px; margin-top: 30px; }}
</style>
"""


def _data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def header_html(title: str, subtitle: str, logo_path: Path, banner_path: Path) -> str:
    banner = (
        f'<div class="banner" style="background-image:url({_data_uri(banner_path)})"></div>'
        if banner_path.is_file()
        else ""
    )
    logo = f'<img class="logo" src="{_data_uri(logo_path)}"/>' if logo_path.is_file() else ""
    return (
        f'<div class="app-header">{banner}{logo}<div class="texts">'
        f"<h1>{escape(title)}</h1><div class=\"sub\">{escape(subtitle)}</div>"
        '<div class="accent"></div></div></div>'
    )


def counter_html(name: str, value: int) -> str:
    color = CLASS_COLORS.get(name, COLOR_PRIMARY)
    return (
        f'<div class="counter" style="border-left-color:{color}">'
        f'<div class="name">{escape(name)}</div>'
        f'<div class="value" style="color:{color}">{value}</div></div>'
    )


def badges_html(items) -> str:
    return '<div class="badges">' + "".join(f'<span class="badge">{escape(i)}</span>' for i in items) + "</div>"


def feature_html(title: str, text: str) -> str:
    return f'<div class="feature"><h4>{escape(title)}</h4><p>{escape(text)}</p></div>'
