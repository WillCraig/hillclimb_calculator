# Hillclimb Calculator

Estimate cycling performance from a GPX route: how long a ride takes at a
constant power output, or how much power a target finish time requires,
and which gear puts you in the optimal cadence range at that speed.

## CLI usage

```sh
python main.py watts <gpx_file> --watts 200
python main.py time  <gpx_file> --target 1:30:00
```

Rider, bike, wheel, and drivetrain values come from `config.json`
(`--config` picks another file). Edit that file to match your setup
before running.

A Streamlit demo with the same model lives in `app.py`; there the same
values are entered in the sidebar instead of `config.json`.

## Gear presets

`config.json` is plain JSON, so it cannot carry comments listing other
gear sizes. Common sizes live in the reference file
[`gear_presets.json`](gear_presets.json) instead. Nothing reads that
file at runtime: copy a preset's `cogs` list into `cassette` and a
preset's `chainrings` list into `chainrings` in `config.json` (or paste
the numbers into the Streamlit sidebar).

Cassettes covered, cog by cog:

- Shimano road: 12-speed 11-30 and 11-34; 11-speed 11-28, 11-30, and
  11-32; plus the 11-speed 11-34 (CS-HG800-11) often paired with GRX
- Shimano MTB/gravel: 12-speed 10-45 and 10-51 (Deore XT, Micro Spline)
- SRAM road: 12-speed 10-28, 10-33, and 10-36 (XDR)
- SRAM MTB: Eagle 12-speed 10-50 and 10-52 (XD)

Chainrings covered: Shimano road doubles 54/40, 52/36, and 50/34; GRX
48/31, 46/30, and 1x 40T/42T; Shimano MTB 1x 30T/32T/34T; SRAM road
doubles 50/37, 48/35, 46/33, and 43/30 Wide; SRAM 1x road/gravel
40T/42T/44T and Eagle MTB 1x 32T/34T.

Only well-known, manufacturer-published ranges are listed. If your exact
cassette is not there, count the teeth on yours and type them into
`config.json` in ascending order — the model only needs the tooth counts.
