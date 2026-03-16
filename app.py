"""
Hillclimb Calculator — Streamlit UI
"""

import math
import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from formatters import fmt_time
from parsegpx import load_route, parse_gpx, smooth_elevation, haversine
from physics import simulate, power_for_time, route_stats, gear_table

st.set_page_config(page_title="Hillclimb Calculator", page_icon="🚴", layout="wide")

WHEEL_BSD_MM = {"700c": 622, '29"': 622, "650b": 584, '27.5"': 584}
DEFAULT_GPX = os.path.join(os.path.dirname(__file__), "sn.gpx")

SOURCE_FILES = {
    "app.py": __file__,
    "physics.py": os.path.join(os.path.dirname(__file__), "physics.py"),
    "parsegpx.py": os.path.join(os.path.dirname(__file__), "parsegpx.py"),
    "formatters.py": os.path.join(os.path.dirname(__file__), "formatters.py"),
    "main.py": os.path.join(os.path.dirname(__file__), "main.py"),
}


def cadence_zone(rpm: float) -> str:
    if rpm < 60:
        return "grinding"
    if rpm < 70:
        return "low"
    if rpm <= 90:
        return "◀ optimal"
    if rpm <= 110:
        return "high"
    return "spinning out"


def parse_time_input(s: str) -> float | None:
    parts = s.strip().split(":")
    try:
        parts = [int(p) for p in parts]
    except ValueError:
        return None
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return None


@st.cache_data
def load_gpx_data(path: str):
    return load_route(path)


def show_results(
    stats: dict,
    avg_speed: float,
    cfg: dict,
    total_time: float = -0.1,
    watts: float = -0.1,
    target_s: float = None,
    power: float = None,
):
    """Render the same output as the CLI — route summary, key numbers, gear table."""

    # Route summary
    dist_mi = stats["distance_m"] / 1609.344
    climb_ft = stats["climb_m"] * 3.28084
    speed_mph = avg_speed * 2.23694

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Distance", f"{dist_mi:.2f} mi")
    c2.metric("Total climb", f"{climb_ft:.0f} ft")
    c3.metric("Avg grade", f"{stats['avg_grade_pct']:.1f}%")
    c4.metric("P95 climb", f"{stats['max_climb_pct']:.1f}%")
    c5.metric("P5 descent", f"{stats['max_desc_pct']:.1f}%")

    st.divider()

    # Mode-specific numbers
    w = watts if watts > 0.0 else power
    wpk = w / cfg["rider_mass_kg"]

    # if total_time is not None:
    if total_time > 0.0:
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Power", f"{watts:.0f} W")
        d2.metric("Watts / kg", f"{wpk:.2f} W/kg")
        d3.metric("Finish time", fmt_time(total_time))
        d4.metric("Average speed", f"{speed_mph:.1f} mph")
    else:
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Target time", fmt_time(target_s))
        d2.metric("Required power", f"{power:.0f} W")
        d3.metric("Watts / kg", f"{wpk:.2f} W/kg")
        d4.metric("Average speed", f"{speed_mph:.1f} mph")

    # Gear table
    st.subheader(f"Gear cadences at {avg_speed * 3.6:.1f} km/h")
    rows = gear_table(avg_speed, cfg)
    df = pd.DataFrame(
        [
            {
                "Gear": r["label"],
                "Ratio": round(r["ratio"], 2),
                "Dev (m)": round(r["dev_m"], 2),
                "Cadence (rpm)": round(r["cadence"]),
                "Zone": cadence_zone(r["cadence"]),
            }
            for r in rows
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Rider & Bike")
    rider_mass = st.number_input("Rider mass (kg)", 40, 200, 95)
    bike_mass = st.number_input("Bike mass (kg)", 3, 30, 10)

    st.divider()
    st.header("Aerodynamics & Rolling")
    cda = st.number_input(
        "CdA (m²)",
        0.15,
        0.80,
        0.42,
        step=0.01,
        format="%.2f",
        help="~0.40 upright · ~0.32 hoods · ~0.25 aero/TT",
    )
    cr = st.number_input(
        "Rolling resistance",
        0.001,
        0.020,
        0.005,
        step=0.001,
        format="%.3f",
        help="~0.003 slicks · ~0.004 road · ~0.008 gravel",
    )

    st.divider()
    st.header("Wheels")
    wheel_size = st.selectbox("Wheel size", list(WHEEL_BSD_MM.keys()))
    tire_width = st.number_input("Tire width (mm)", 18, 60, 28)
    circ = math.pi * (WHEEL_BSD_MM[wheel_size] + 2 * tire_width) / 1000
    st.caption(f"Circumference: {circ:.4f} m")

    st.divider()
    st.header("Drivetrain")
    chainrings = [int(x) for x in st.text_input("Chainrings", "34, 50").split(",")]
    cassette = [
        int(x)
        for x in st.text_input("Cassette", "11, 13, 15, 17, 19, 21, 24, 28, 32").split(
            ","
        )
    ]

cfg = {
    "rider_mass_kg": rider_mass,
    "bike_mass_kg": bike_mass,
    "cda": cda,
    "rolling_resistance": cr,
    "wheel_circumference_m": circ,
    "chainrings": chainrings,
    "cassette": cassette,
}

# ── Main ──────────────────────────────────────────────────────────────────────

st.title("🚴 Hillclimb Calculator")

tab_calc, tab_profile, tab_code = st.tabs(["Calculate", "Route Profile", "Source Code"])

with tab_calc:
    segments, smoothed_ele = load_gpx_data(DEFAULT_GPX)
    stats = route_stats(segments, smoothed_ele)

    mode = st.radio(
        "Mode",
        [
            "Given watts → estimate finish time",
            "Given target time → find required watts",
        ],
        horizontal=True,
    )
    st.write("")

    if mode == "Given watts → estimate finish time":
        watts = st.number_input("Sustained power (W)", 50, 1500, 200)
        if st.button("Calculate", type="primary"):
            total_time, avg_speed = simulate(segments, watts, cfg)
            show_results(stats, avg_speed, cfg, total_time=total_time, watts=watts)

    else:
        target_input = st.text_input(
            "Target finish time", "1:30:00", placeholder="h:mm:ss or mm:ss"
        )
        if st.button("Calculate", type="primary"):
            target_s = parse_time_input(target_input)
            if target_s is None:
                st.error("Could not parse time — use h:mm:ss or mm:ss.")
            else:
                power = power_for_time(segments, target_s, cfg)
                _, avg_speed = simulate(segments, power, cfg)
                show_results(stats, avg_speed, cfg, target_s=target_s, power=power)

with tab_profile:
    points = parse_gpx(DEFAULT_GPX)
    smoothed = smooth_elevation(points)
    cum_dist = [0.0]
    for i in range(1, len(points)):
        cum_dist.append(cum_dist[-1] + haversine(points[i - 1], points[i]) / 1000)

    fig = go.Figure(
        go.Scatter(
            x=cum_dist,
            y=smoothed,
            mode="lines",
            fill="tozeroy",
            line=dict(color="#1f77b4", width=2),
        )
    )
    fig.update_layout(
        xaxis_title="Distance (km)",
        yaxis_title="Elevation (m)",
        margin=dict(l=0, r=0, t=8, b=0),
        height=320,
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

with tab_code:
    chosen = st.selectbox("File", list(SOURCE_FILES.keys()))
    with open(SOURCE_FILES[chosen]) as fh:
        st.code(fh.read(), language="python")
