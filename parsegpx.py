import math
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional

# ── GPX parsing ───────────────────────────────────────────────────────────────

GPX_NS = "http://www.topografix.com/GPX/1/1"


@dataclass
class TrackPoint:
    lat: float
    lon: float
    ele: float
    time: Optional[str]


def parse_gpx(filepath: str) -> list[TrackPoint]:
    tree = ET.parse(filepath)
    root = tree.getroot()
    points = []
    for trkpt in root.findall(f".//{{{GPX_NS}}}trkpt"):
        lat = float(trkpt.attrib["lat"])
        lon = float(trkpt.attrib["lon"])
        ele_el = trkpt.find(f"{{{GPX_NS}}}ele")
        ele = float(ele_el.text) if ele_el is not None and ele_el.text else 0.0
        time_el = trkpt.find(f"{{{GPX_NS}}}time")
        points.append(
            TrackPoint(lat, lon, ele, time_el.text if time_el is not None else None)
        )
    return points


def haversine(p1: TrackPoint, p2: TrackPoint) -> float:
    """Horizontal distance in metres between two TrackPoints."""
    R = 6_371_000
    lat1, lat2 = math.radians(p1.lat), math.radians(p2.lat)
    dlat = lat2 - lat1
    dlon = math.radians(p2.lon - p1.lon)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


def gaussian_weights(window_size: int, sigma: float) -> list[float]:
    half = window_size // 2
    weights = [math.exp(-0.5 * (i / sigma) ** 2) for i in range(-half, half + 1)]
    total = sum(weights)
    return [w / total for w in weights]


def smooth_elevation(
    points: list[TrackPoint], window_size: int = 11, sigma: float = 3.0
) -> list[float]:
    """Gaussian-smooth the elevation signal to reduce GPS noise before computing gradients."""
    raw = [p.ele for p in points]
    weights = gaussian_weights(window_size, sigma)
    half = window_size // 2
    smoothed = []
    for i in range(len(raw)):
        total = weight_sum = 0.0
        for j, w in enumerate(weights):
            idx = i + j - half
            if 0 <= idx < len(raw):
                total += raw[idx] * w
                weight_sum += w
        smoothed.append(total / weight_sum)
    return smoothed


def build_segments(points: list[TrackPoint], smoothed_ele: list[float]) -> list[dict]:
    """
    Convert TrackPoints into route segments.
    Each segment has the true 3-D distance (m) and rise/run gradient.
    Using smoothed elevation avoids noisy gradient spikes from raw GPS data.
    """
    segments = []
    for i in range(1, len(points)):
        horiz = haversine(points[i - 1], points[i])
        rise = smoothed_ele[i] - smoothed_ele[i - 1]
        dist = math.sqrt(horiz**2 + rise**2)
        gradient = rise / horiz if horiz > 0.5 else 0.0
        segments.append({"distance": dist, "gradient": gradient})
    return segments


def load_route(gpx_path: str) -> tuple[list[dict], list[float]]:
    """GPX file → TrackPoints → smoothed elevation → segments."""
    points = parse_gpx(gpx_path)
    if len(points) < 2:
        sys.exit("Error: GPX file contains fewer than two track points.")
    smoothed_ele = smooth_elevation(points)
    return build_segments(points, smoothed_ele), smoothed_ele
