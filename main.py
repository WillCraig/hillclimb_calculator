#!/usr/bin/env python3
"""
Hillclimb Calculator

Usage:
  python main.py watts  <gpx_file> --watts 200
  python main.py time   <gpx_file> --target 1:30:00

'watts' — given a constant power output, show how long the ride takes
          and which gear puts you in the optimal cadence range.

'time'  — given a target finish time, find the sustained power required
          and which gear hits optimal cadence at that speed.
"""

import argparse
import json
from physics import simulate, power_for_time, route_stats
from parsegpx import load_route
from formatters import (
    watts_output,
    print_time_output,
    parse_time,
)


# ── Config ────────────────────────────────────────────────────────────────────


def load_config(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


# ── Commands ──────────────────────────────────────────────────────────────────


def cmd_watts(args):
    cfg = load_config(args.config)
    segments, smoothed_ele = load_route(args.gpx_file)
    stats = route_stats(segments, smoothed_ele)
    total_time, avg_speed = simulate(segments, args.watts, cfg)

    watts_output(stats, args, avg_speed, cfg, total_time)


def cmd_time(args):
    cfg = load_config(args.config)
    segments, smoothed_ele = load_route(args.gpx_file)
    stats = route_stats(segments, smoothed_ele)
    target_s = parse_time(args.target)
    power = power_for_time(segments, target_s, cfg)
    _, avg_speed = simulate(segments, power, cfg)

    print_time_output(stats, power, avg_speed, cfg, args, target_s)


# ── Entry point ───────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Estimate cycling performance from a GPX route."
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to config file (default: config.json)",
    )
    parser.add_argument(
        "--usa",
        default=True,
        help="Use USA-style units and time format (default: False)",
        action="store_true",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_watts = sub.add_parser("watts", help="Simulate ride at a fixed wattage.")
    p_watts.add_argument("gpx_file")
    p_watts.add_argument(
        "--watts",
        "-w",
        type=float,
        required=True,
        help="Constant power output in watts",
    )

    p_time = sub.add_parser("time", help="Find power needed for a target finish time.")
    p_time.add_argument("gpx_file")
    p_time.add_argument(
        "--target",
        "-t",
        required=True,
        metavar="hh:mm:ss",
        help="Target finish time, e.g. 1:30:00 or 45:00",
    )

    args = parser.parse_args()
    if args.command == "watts":
        cmd_watts(args)
    elif args.command == "time":
        cmd_time(args)


if __name__ == "__main__":
    main()
