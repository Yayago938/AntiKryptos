"""
SENTINEL-X Input Handlers
Auto-detects input type and extracts clean text for the analysis pipeline.
Handlers: plain text, URL, PDF, image (OCR), VPN/access log (JSON)

FIX: handle_pdf() now appends hidden white-font text into content
     so the security gate and model can see it.
"""

import re
import json
import math
from typing import Optional


# ---------------------------------------------------------------------------
# TYPE DETECTION
# ---------------------------------------------------------------------------

URL_RE = re.compile(
    r'^(https?://|www\.)[^\s]{4,}',
    re.IGNORECASE
)

def detect_input_type(raw: str, filename: Optional[str] = None) -> str:
    """Returns one of: text | url | pdf | image | vpn_log"""
    if filename:
        ext = filename.lower().rsplit(".", 1)[-1]
        if ext == "pdf":
            return "pdf"
        if ext in ("png", "jpg", "jpeg", "webp", "bmp", "tiff"):
            return "image"
        if ext == "json":
            return "vpn_log"

    stripped = raw.strip()

    if stripped.startswith("{") or stripped.startswith("["):
        try:
            json.loads(stripped)
            return "vpn_log"
        except json.JSONDecodeError:
            pass

    if URL_RE.match(stripped):
        return "url"

    return "text"


# ---------------------------------------------------------------------------
# HANDLER 1: Plain text
# ---------------------------------------------------------------------------

def handle_text(text: str) -> dict:
    return {
        "type": "text",
        "content": text.strip(),
        "meta": {"char_count": len(text.strip())},
    }


# ---------------------------------------------------------------------------
# HANDLER 2: URL
# ---------------------------------------------------------------------------

def handle_url(url: str) -> dict:
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {"User-Agent": "Mozilla/5.0 (SENTINEL-X Security Scanner)"}
        resp = requests.get(url, timeout=8, headers=headers, allow_redirects=True)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "noscript", "meta", "head"]):
            tag.decompose()

        visible_text = soup.get_text(separator=" ", strip=True)
        redirect_chain = [r.url for r in resp.history] + [resp.url]

        return {
            "type": "url",
            "content": visible_text[:8000],
            "meta": {
                "final_url": resp.url,
                "status_code": resp.status_code,
                "redirect_chain": redirect_chain,
                "redirect_count": len(resp.history),
                "content_type": resp.headers.get("Content-Type", ""),
            },
        }
    except Exception as e:
        return {
            "type": "url",
            "content": f"[URL fetch failed: {str(e)}]",
            "meta": {"error": str(e)},
        }


# ---------------------------------------------------------------------------
# HANDLER 3: PDF
# FIX: hidden white-font text is now appended to content, not only stored
#      in meta — so the gate and model see it.
# ---------------------------------------------------------------------------

def handle_pdf(file_bytes: bytes) -> dict:
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        all_text = []
        hidden_text_found = []
        page_count = doc.page_count

        for page_num in range(page_count):
            page = doc[page_num]
            all_text.append(page.get_text("text"))

            blocks = page.get_text("rawdict")["blocks"]
            for block in blocks:
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        color = span.get("color", 0)
                        text = span.get("text", "").strip()
                        # White (#FFFFFF) or near-white text
                        if color in (16777215, 16777214, 16711422) and text:
                            hidden_text_found.append(text)

        full_text = "\n".join(all_text)

        # FIX: append hidden text into content so gate + model can analyse it
        if hidden_text_found:
            full_text += "\n[HIDDEN TEXT DETECTED]\n" + " ".join(hidden_text_found)

        return {
            "type": "pdf",
            "content": full_text,
            "meta": {
                "page_count": page_count,
                "hidden_text_found": hidden_text_found,
                "hidden_text_count": len(hidden_text_found),
                "hidden_text_preview": hidden_text_found[:5],
            },
        }
    except Exception as e:
        return {
            "type": "pdf",
            "content": f"[PDF extraction failed: {str(e)}]",
            "meta": {"error": str(e)},
        }


# ---------------------------------------------------------------------------
# HANDLER 4: Image — OCR
# ---------------------------------------------------------------------------

def handle_image(file_bytes: bytes) -> dict:
    try:
        import pytesseract
        from PIL import Image
        import io

        image = Image.open(io.BytesIO(file_bytes))
        text = pytesseract.image_to_string(image)

        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        confidences = [int(c) for c in data["conf"] if str(c).isdigit() and int(c) > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        return {
            "type": "image",
            "content": text.strip(),
            "meta": {
                "image_size": f"{image.width}x{image.height}",
                "ocr_confidence": round(avg_confidence, 2),
                "word_count": len(text.split()),
            },
        }
    except Exception as e:
        return {
            "type": "image",
            "content": f"[OCR failed: {str(e)}]",
            "meta": {"error": str(e)},
        }


# ---------------------------------------------------------------------------
# HANDLER 5: VPN / Access Log — impossible travel detection
# ---------------------------------------------------------------------------

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


MAX_SPEED_KMH = 1000.0


def handle_vpn_log(raw: str) -> dict:
    try:
        events = json.loads(raw)
        if isinstance(events, dict):
            events = [events]

        events_sorted = sorted(events, key=lambda e: e.get("timestamp", 0))
        flags = []
        narrative_parts = []

        for i in range(1, len(events_sorted)):
            prev, curr = events_sorted[i - 1], events_sorted[i]

            if not all(k in prev and k in curr for k in ("lat", "lon", "timestamp")):
                continue

            dt_seconds = curr["timestamp"] - prev["timestamp"]
            if dt_seconds <= 0:
                continue

            dist_km = _haversine_km(prev["lat"], prev["lon"], curr["lat"], curr["lon"])
            speed_kmh = (dist_km / dt_seconds) * 3600

            if speed_kmh > MAX_SPEED_KMH:
                flag = {
                    "event_index": i,
                    "from_ip": prev.get("ip", "unknown"),
                    "to_ip": curr.get("ip", "unknown"),
                    "from_location": f"{prev.get('lat')},{prev.get('lon')}",
                    "to_location": f"{curr.get('lat')},{curr.get('lon')}",
                    "distance_km": round(dist_km, 1),
                    "time_delta_seconds": dt_seconds,
                    "speed_kmh": round(speed_kmh, 1),
                    "verdict": "IMPOSSIBLE_TRAVEL",
                }
                flags.append(flag)
                narrative_parts.append(
                    f"Login from {prev.get('ip')} then {curr.get('ip')} — "
                    f"{round(dist_km)} km in {dt_seconds}s ({round(speed_kmh)} km/h)."
                )

        narrative = " ".join(narrative_parts) if narrative_parts else "No impossible travel detected."

        return {
            "type": "vpn_log",
            "content": narrative,
            "meta": {
                "event_count": len(events_sorted),
                "impossible_travel_flags": flags,
                "anomaly_count": len(flags),
            },
        }
    except Exception as e:
        return {
            "type": "vpn_log",
            "content": f"[VPN log parse failed: {str(e)}]",
            "meta": {"error": str(e)},
        }


# ---------------------------------------------------------------------------
# UNIFIED ROUTER
# ---------------------------------------------------------------------------

def route_input(
    raw: str = "",
    file_bytes: bytes = None,
    filename: str = None,
) -> dict:
    """
    Single entry point. Pass either raw text/URL/JSON string,
    or file_bytes + filename for PDF/image inputs.
    Returns a unified dict with keys: type, content, meta.
    """
    input_type = detect_input_type(raw, filename)

    if input_type == "pdf" and file_bytes:
        return handle_pdf(file_bytes)
    elif input_type == "image" and file_bytes:
        return handle_image(file_bytes)
    elif input_type == "url":
        return handle_url(raw)
    elif input_type == "vpn_log":
        return handle_vpn_log(raw)
    else:
        return handle_text(raw)