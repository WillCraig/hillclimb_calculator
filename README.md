# 🚴 Hillclimb Calculator

**How fast will you climb it — and in what gear?** The Hillclimb Calculator takes a GPX route and your rider/bike setup, then answers the two questions every cyclist asks before a big climb: *"If I hold this power, how long will it take?"* and *"What power do I need to hit my target time?"* It also shows which gear combinations keep your cadence in a comfortable range at that speed, so you can pace the effort and pick your gearing before you ever clip in. It's for road and gravel riders planning a climb, a hill-climb event, or a pacing strategy for a hilly route.

## ▶ Try the live demo

**[willc-hillclimb-calculator-demo.streamlit.app](https://willc-hillclimb-calculator-demo.streamlit.app/)**

No install needed — open the demo, set your rider and bike numbers in the sidebar, and calculate. The demo runs the bundled sample route (`sn.gpx`); use the command-line version below to run your own GPX files.

## What it does

- **Watts → time:** hold a constant power and get an estimated finish time, average speed, and W/kg.
- **Target time → watts:** set a goal time and get the sustained power (and W/kg) required to hit it.
- **Route summary:** distance, total climb, average grade, and steepest-typical climb/descent grades (95th/5th percentile, so one noisy GPS point doesn't dominate).
- **Gear cadence table:** every chainring × cassette combination with gear ratio, development, and cadence at the estimated average speed, flagged as *grinding*, *low*, *optimal*, *high*, or *spinning out*.
- **Route profile (web app):** an elevation chart of the route, plus a tab to browse the source code.

Under the hood it parses the GPX track, Gaussian-smooths the elevation to tame GPS noise, splits the route into segments, and solves the standard cycling power equation — gravity, rolling resistance, and aerodynamic drag — segment by segment (see `physics.py`).

**Honest limits:** this is a planning estimate, not a race prediction. It assumes perfectly constant power, sea-level air density, and no wind, braking, coasting, traffic, or fatigue. Treat the numbers as a pacing guide, not a guarantee.

## Quick start (command line)

Requires Python 3.

```bash
git clone https://github.com/WillCraig/hillclimb_calculator.git
cd hillclimb_calculator
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Edit `config.json` to match you and your bike (see [Configuration](#configuration)), then:

```bash
# How long will the sample route take at a steady 200 W?
python main.py watts sn.gpx --watts 200
```

Output (gear table truncated):

```
  Route:          11.61 mi   ↑ 2801 ft   avg grade 4.6%   p95 climb 20.1% / descent 0.0%
  Power:          200 W
  Watts per kilogram: 2.11 W/kg
  Total time:     1h 24m 40s
  Average speed:  8.2 mph

  Gear cadences at 13.2 km/h:
  Gear       Ratio    Dev (m)    Cadence (rpm)    Zone
  ────────────────────────────────────────────────────────
  34×32      1.06     2.26       97               ◀ optimal
  34×28      1.21     2.59       85               ◀ optimal
  ... (remaining gears omitted)
```

Run the same commands with your own `.gpx` file exported from any route planner or GPS device (GPX 1.1 track points; elevation is used when present). Two sample routes are included: `sn.gpx` and `test.gpx`.

### CLI reference

```
python main.py [--config CONFIG] watts <gpx_file> --watts WATTS
python main.py [--config CONFIG] time  <gpx_file> --target hh:mm:ss
```

| Command | Meaning |
|---|---|
| `watts` (`--watts` / `-w`) | Simulate the ride at a fixed power in watts; prints finish time, average speed, W/kg, and the gear table. |
| `time` (`--target` / `-t`) | Find the constant power needed to finish in the target time (`h:mm:ss` or `mm:ss`, e.g. `1:30:00` or `45:00`). |
| `--config` | Path to an alternate config file (default: `config.json`). Global option — put it before the subcommand. |

> **Known issue:** the CLI `time` command currently crashes with `KeyError: 'rider_weight_kg'` in `formatters.py` after printing the required power. The target-time calculation itself works in the [Streamlit app](#web-app-streamlit) — use that for target-time mode until the CLI formatter is fixed.

## Web app (Streamlit)

After the install steps above:

```bash
streamlit run app.py
```

The app opens in your browser with:

- **Sidebar controls** for rider/bike mass, CdA, rolling resistance, wheel size and tire width, chainrings, and cassette — the same inputs as `config.json`, no file editing needed.
- **Calculate tab:** both modes (watts → time, target time → watts) with route stats, key numbers, and the gear table.
- **Route Profile tab:** elevation profile of the route.
- **Source Code tab:** browse the Python source in the browser.

The web app currently always uses the bundled `sn.gpx` route (there is no GPX upload yet). For your own routes, use the CLI.

## Configuration

The CLI reads `config.json` in the working directory (or the file given by `--config`). Edit the values to match your setup:

| Key | Meaning | Default |
|---|---|---|
| `rider_mass_kg` | Rider mass in kg | `95` |
| `bike_mass_kg` | Bike mass in kg | `10` |
| `cda` | Drag coefficient × frontal area (m²). ~0.40 upright, ~0.32 hoods, ~0.25 aero/TT | `0.42` |
| `rolling_resistance` | ~0.003 racing slicks, ~0.004 road tyres, ~0.008 gravel | `0.005` |
| `wheel_size` | One of `700c`, `29`, `650b`, `27.5` | `"700c"` |
| `tire_width_mm` | Tire width in mm; wheel circumference is derived from size + width | `28` |
| `chainrings` | Front chainring tooth counts | `[34, 50]` |
| `cassette` | Rear cog tooth counts | `[11, 13, 15, 17, 19, 21, 24, 28, 32]` |

You can instead set `wheel_circumference_m` directly and omit `wheel_size`/`tire_width_mm`.

## Project files

| File | Purpose |
|---|---|
| `main.py` | Command-line interface (`watts` / `time` subcommands) |
| `app.py` | Streamlit web app (the live demo) |
| `physics.py` | Cycling physics model, ride simulation, gear/cadence math |
| `parsegpx.py` | GPX parsing, elevation smoothing, segment building |
| `formatters.py` | CLI output formatting and time parsing |
| `config.json` | Rider/bike setup for the CLI |
| `requirements.txt` | Python dependencies (`numpy` for the CLI, plus `streamlit` and `pandas` for the web app) |
| `sn.gpx`, `test.gpx` | Sample routes |

---

**[Try it live →](https://willc-hillclimb-calculator-demo.streamlit.app/)** Pick your watts, see your time, choose your gear — then go climb it.
