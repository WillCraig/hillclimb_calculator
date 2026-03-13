"""
Cycling physics model.

Core equation:  P = v * (F_gravity + F_rolling + F_drag)

  F_gravity = m * g * sin(θ)          — force pulling the rider back on a slope
  F_rolling = m * g * Cr * cos(θ)     — rolling resistance
  F_drag    = 0.5 * ρ * CdA * v²      — aerodynamic drag

Rearranging for v gives a cubic equation:
  (0.5·ρ·CdA)·v³  +  (m·g·sinθ + m·g·Cr·cosθ)·v  −  P  =  0

We solve this numerically with numpy and pick the single real positive root.
"""

import math

import numpy as np

G = 9.81    # m/s²  gravitational acceleration
RHO = 1.225  # kg/m³  air density at sea level


# ── Speed from power ──────────────────────────────────────────────────────────

def solve_speed(power_w: float, gradient: float, mass_kg: float, cda: float, cr: float) -> float:
    """
    Return the speed (m/s) a rider sustains at constant power on a given gradient.

    Solves:  a·v³ + c·v − P = 0   where
      a = 0.5 · ρ · CdA
      c = m·g·sinθ + m·g·Cr·cosθ
    """
    theta = math.atan(gradient)
    f_const = mass_kg * G * math.sin(theta) + mass_kg * G * cr * math.cos(theta)

    # numpy.roots expects highest-degree first: [a, 0, c, -P]
    roots = np.roots([0.5 * RHO * cda, 0.0, f_const, -power_w])

    # The cubic always has one real positive root for physically valid inputs
    real_positive = [r.real for r in roots if abs(r.imag) < 1e-6 and r.real > 0.01]
    return max(real_positive) if real_positive else 0.01


# ── Ride simulation ───────────────────────────────────────────────────────────

def simulate(segments: list[dict], power_w: float, config: dict) -> tuple[float, float]:
    """
    Simulate a ride at constant power across all segments.

    Returns (total_time_s, avg_speed_ms).
    We solve for speed independently on each segment — think of it as the
    pipeline: [gradient] → [speed] → [time] → sum.
    """
    mass = config["rider_mass_kg"] + config["bike_mass_kg"]
    cda = config["cda"]
    cr = config["rolling_resistance"]

    total_time = 0.0
    total_dist = 0.0

    for seg in segments:
        d = seg["distance"]
        if d < 0.5:     # skip GPS noise micro-segments
            continue
        v = solve_speed(power_w, seg["gradient"], mass, cda, cr)
        total_time += d / v
        total_dist += d

    avg_speed = total_dist / total_time if total_time > 0 else 0.0
    return total_time, avg_speed


def power_for_time(segments: list[dict], target_s: float, config: dict) -> float:
    """
    Binary-search for the constant power output that makes the ride finish
    in exactly target_s seconds.

    Lower wattage → slower → more time, so we search the power range [1, 3000] W.
    60 iterations gives sub-watt precision.
    """
    lo, hi = 1.0, 3000.0
    for _ in range(60):
        mid = (lo + hi) / 2.0
        t, _ = simulate(segments, mid, config)
        if t > target_s:
            lo = mid   # too slow, need more power
        else:
            hi = mid   # too fast, need less power
    return (lo + hi) / 2.0


# ── Gear cadences ─────────────────────────────────────────────────────────────

def gear_table(speed_ms: float, config: dict) -> list[dict]:
    """
    For every front/rear gear combination, calculate the cadence (RPM) needed
    to hold the given speed.

      development (m/rev) = (chainring_teeth / cog_teeth) × wheel_circumference
      cadence_rpm         = (speed_ms / development) × 60

    Returns rows sorted by gear ratio (lowest → highest).
    """
    circ = config["wheel_circumference_m"]
    rows = []
    for front in config["chainrings"]:
        for rear in config["cassette"]:
            dev = (front / rear) * circ
            cadence = (speed_ms / dev) * 60
            rows.append({
                "label":   f"{front}×{rear}",
                "ratio":   front / rear,
                "dev_m":   dev,
                "cadence": cadence,
            })
    return sorted(rows, key=lambda r: r["ratio"])


# ── Route summary ─────────────────────────────────────────────────────────────

def route_stats(segments: list[dict], smoothed_ele: list[float]) -> dict:
    total_dist = sum(s["distance"] for s in segments)
    total_climb = sum(
        max(0.0, smoothed_ele[i] - smoothed_ele[i - 1])
        for i in range(1, len(smoothed_ele))
    )
    gradients = [s["gradient"] for s in segments]
    return {
        "distance_m":    total_dist,
        "climb_m":       total_climb,
        # 95th/5th percentile avoids single noisy GPS points dominating the stat
        "max_climb_pct": float(np.percentile(gradients, 95)) * 100,
        "max_desc_pct":  float(np.percentile(gradients,  5)) * 100,
        "avg_grade_pct": (total_climb / total_dist * 100) if total_dist > 0 else 0.0,
    }
