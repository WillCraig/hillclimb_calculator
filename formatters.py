import sys
from physics import gear_table


def fmt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h}h {m:02d}m {s:02d}s" if h else f"{m}m {s:02d}s"


def parse_time(s: str) -> float:
    """Accept hh:mm:ss or mm:ss, return total seconds."""
    parts = s.strip().split(":")
    try:
        parts = [int(p) for p in parts]
    except ValueError:
        sys.exit(f"Error: cannot parse time '{s}'. Use mm:ss or hh:mm:ss.")
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    sys.exit(f"Error: use mm:ss or hh:mm:ss, got '{s}'.")


def print_gear_table(speed_ms: float, config: dict):
    rows = gear_table(speed_ms, config)
    speed_kph = speed_ms * 3.6
    print(f"\n  Gear cadences at {speed_kph:.1f} km/h:")
    print(f"  {'Gear':<10} {'Ratio':<8} {'Dev (m)':<10} {'Cadence (rpm)':<16} Zone")
    print("  " + "─" * 56)
    for r in rows:
        if r["cadence"] < 60:
            zone = "grinding"
        elif r["cadence"] < 70:
            zone = "low"
        elif r["cadence"] <= 100:
            zone = "◀ optimal"
        elif r["cadence"] <= 110:
            zone = "high"
        else:
            zone = "spinning out"
        print(
            f"  {r['label']:<10} {r['ratio']:<8.2f} {r['dev_m']:<10.2f} {r['cadence']:<16.0f} {zone}"
        )


def print_route_header(stats: dict, usa_mode: bool) -> None:
    distance = stats["distance_m"] / 1000
    climb = stats["climb_m"]
    climb_lbl = "m"
    if usa_mode:
        distance *= 0.621371
        climb *= 3.28084
        climb_lbl = "ft"
        unit_dist = "mi"
    else:
        unit_dist = "km"
    print(
        f"\n  Route:          {distance:.2f} {unit_dist}   "
        f"↑ {climb:.0f} {climb_lbl}   "
        f"avg grade {stats['avg_grade_pct']:.1f}%   "
        f"p95 climb {stats['max_climb_pct']:.1f}% / descent {stats['max_desc_pct']:.1f}%"
    )


def watts_output(stats, args, avg_speed, cfg, total_time) -> None:
    speed = avg_speed * 3.6
    if args.usa:
        speed *= 0.621371
        unit_speed = "mph"
    else:
        unit_speed = "km/h"

    print_route_header(stats, args.usa)
    print(f"  Power:          {args.watts:.0f} W")
    print(f"  Watts per kilogram: {args.watts / cfg['rider_mass_kg']:.2f} W/kg")
    print(f"  Total time:     {fmt_time(total_time)}")
    print(f"  Average speed:  {speed:.1f} {unit_speed}")
    print_gear_table(avg_speed, cfg)
    print()


def print_time_output(stats, power, avg_speed, cfg, args, target_s) -> None:
    speed = avg_speed * 3.6
    if args.usa:
        speed *= 0.621371
        unit_speed = "mph"
    else:
        unit_speed = "km/h"

    print_route_header(stats, args.usa)
    print(f"  Target time:    {fmt_time(target_s)}")
    print(f"  Required power: {power:.0f} W")
    print(f"  Watts per kilogram: {power / cfg['rider_weight_kg']:.2f} W/kg")
    print(f"  Average speed:  {speed:.1f} {unit_speed}")
    print_gear_table(avg_speed, cfg)
    print()
