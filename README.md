<div align="center">

# 🌞 Solar-Aware GA Multi-Sink WSN

### A Genetic-Algorithm-based, solar-energy-aware, multi-sink data aggregation protocol for Wireless Sensor Networks

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![NumPy](https://img.shields.io/badge/numpy-1.20+-orange.svg)](https://numpy.org/)
[![Matplotlib](https://img.shields.io/badge/matplotlib-3.4+-yellow.svg)](https://matplotlib.org/)
[![Status](https://img.shields.io/badge/status-research-green.svg)]()
[![Docs](https://img.shields.io/badge/docs-comprehensive-brightgreen.svg)](#-documentation)

*A simulation framework that pits a smart **Genetic-Algorithm + Solar-Aware Multi-Sink** routing protocol against the classic **LEACH** baseline — and shows just how much battery life you can save.*

[**Quick Start**](#-quick-start) ·
[**Architecture**](#-architecture) ·
[**Documentation**](#-documentation) ·
[**Results**](#-example-results) ·
[**References**](#-references)

</div>

---

## 📖 Overview

Wireless Sensor Networks (WSNs) power **smart agriculture**, **forest-fire detection**, **smart cities**, and **industrial IoT** — but tiny battery-powered sensors die fast if they shout long-distance to a base station. This project explores a smarter way to keep them alive.

We simulate a 100 m × 100 m field of solar-equipped sensor nodes and compare:

| | 🔴 LEACH (baseline) | 🔵 Solar-Aware GA Multi-Sink (ours) |
|---|---|---|
| **CH selection** | Random dice roll | Genetic Algorithm with 4-component fitness |
| **Architecture** | 2-tier (sensor → CH → BS) | 3-tier (sensor → CH → MS-CH → BS) |
| **Solar awareness** | None | Energy + sun + centrality + BS-distance |
| **Mid-round safety** | None | MS-CH re-election when battery < 15% |
| **Energy delivered to BS** | Baseline | **Significantly more** |

> **TL;DR — Same hardware, smarter choices, longer life.**

---

## ✨ Key Features

- 🧬 **Genetic Algorithm** for cluster-head election with adaptive mutation, elitism, and early stopping
- ☀️ **Solar-aware** scoring that values nodes currently bathed in sunlight, not just ones with full batteries
- 🎯 **Multi-sink architecture** with MS-CH super-leaders that relay traffic from far CHs
- ⚡ **Vectorised NumPy fitness evaluation** — handles up to 5000 nodes
- 🔄 **Mid-round MS-CH re-election** prevents super-leader collapse
- 📊 **Side-by-side LEACH benchmarking** for honest comparison
- 🖼️ **Topology snapshots** every N rounds with role-coded visualisation
- 📈 **Six-panel results plot** showing lifetime, energy, deaths, balance, and solar cycle
- 🎛️ **Interactive CLI** with sensible defaults — press Enter to skip prompts
- 📚 **Comprehensive documentation** — plain-English guides + formula-level deep-dive

---

## 🏗️ Architecture

The smart protocol uses a **three-tier hierarchy**:

```
                  ┌──────────────────────────────┐
                  │       🛰️  Base Station         │
                  └──────────────▲───────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
       Path A │ direct       Path B (via relay)     │ Path A direct
        (close + healthy)        (far or weak)
              │                  │                  │
              │           ┌──────┴──────┐           │
              │           │   ⭐ MS-CH    │           │
              │           └─────▲───────┘           │
              │                 │                   │
              │      ┌──────────┴──────────┐        │
              │      │                     │        │
        ┌─────┴──┐ ┌─┴────┐ ┌────┐    ┌────┴───┐   │
        │   CH   │ │  CH  │ │ CH │    │   CH   │   │
        └────▲───┘ └──▲───┘ └─▲──┘    └───▲────┘   │
             │        │       │           │        │
       (whisper)  (whisper) (whisper)  (whisper)   │
             │        │       │           │        │
        ┌────┴──┐  ┌──┴─┐  ┌──┴─┐      ┌──┴─┐      │
        │sensor │  │ s  │  │ s  │      │ s  │  ... │
        └───────┘  └────┘  └────┘      └────┘      │
```

**Tier 1 — Sensor nodes:** sense data, whisper to nearest CH
**Tier 2 — Cluster Heads (CH):** aggregate, then choose Path A (direct) or Path B (relay)
**Tier 3 — MS-CH super-leaders:** collect from relay CHs, aggregate again, ship to BS

📘 *For the full story see [`HOW_SOLAR_GA_WSN_WORKS.md`](HOW_SOLAR_GA_WSN_WORKS.md). For the math, see [`SOLAR_GA_WSN_TECHNICAL_DEEP_DIVE.md`](SOLAR_GA_WSN_TECHNICAL_DEEP_DIVE.md).*

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or later
- pip

### Installation

```bash
git clone https://github.com/Imperial-Dragan/Solar_Aware_Multi_Sink.git
cd Solar_Aware_Multi_Sink
pip install -r requirements.txt
```

### Run the simulations

| Command | What it does |
|---|---|
| `python solar_ga_wsn.py` | **Runs both protocols head-to-head** (recommended) |
| `python ga_only.py` | Runs only the Solar-Aware GA Multi-Sink protocol |
| `python leach_only.py` | Runs only the LEACH baseline |

Each script asks you a few setup questions. **Press Enter to accept defaults** — they are calibrated for a 50-node, 100×100m, 300-round demo that runs in about a minute.

### Sample interaction

```
  -- Network Setup --
  Field size in metres (square) [100]:
  Number of sensor nodes [50]:
  Base station X position (metres) [50]:
  Base station Y position (metres) [120]:
  Number of simulation rounds [300]:
  ...
```

---

## 📊 Example Results

After a typical 50-node, 300-round run, you'll see something like:

```
══════════════════════════════════════════════════════════════
  Metric                          LEACH      GA       Winner
  ───────────────────────────────────────────────────────────
  First node death (round)        87        134       GA  ✓
  Network lifetime (rounds)       245       298+      GA  ✓
  Packets delivered to BS         1,920     2,640     GA  ✓
  Final residual energy (J)       0.04      1.82      GA  ✓
  Energy std dev (lower=better)   0.087     0.041     GA  ✓
══════════════════════════════════════════════════════════════
```

### Generated outputs

- 📷 `comparison_results.png` — six-panel side-by-side graphs
- 📁 `topology_snapshots/` — round-by-round topology images for both protocols
- 📺 Live terminal status updates during the run

---

## 📁 Repository Structure

```
Solar_Aware_Multi_Sink/
│
├── 📜 Source code
│   ├── solar_ga_wsn.py            # ★ Main combined runner (LEACH vs GA)
│   ├── ga_only.py                 # GA-only spin-off (no LEACH)
│   └── leach_only.py              # LEACH-only spin-off (baseline)
│
├── 📚 Documentation
│   ├── README.md                  # ← you are here
│   ├── HOW_SOLAR_GA_WSN_WORKS.md  # Plain-English: combined runner
│   ├── HOW_GA_ONLY_WORKS.md       # Plain-English: GA-only file
│   ├── HOW_LEACH_ONLY_WORKS.md    # Plain-English: LEACH baseline
│   └── SOLAR_GA_WSN_TECHNICAL_DEEP_DIVE.md  # Formula-by-formula reference
│
├── 📦 Configuration
│   ├── requirements.txt           # Python dependencies
│   └── .gitignore                 # Ignore generated images/cache
│
└── 📂 Generated at runtime (gitignored)
    ├── topology_snapshots/        # Per-round topology PNGs
    ├── comparison_results.png     # Final comparison graph
    └── leach_results.png          # LEACH-only graph (if run alone)
```

---

## 📚 Documentation

This repo ships with **four layered guides** so anyone — coder or not — can dive in at the right level:

| Document | For | What's inside |
|---|---|---|
| [📘 **HOW_SOLAR_GA_WSN_WORKS.md**](HOW_SOLAR_GA_WSN_WORKS.md) | Non-coders | The "boxing match" framing of LEACH vs GA, written as a story |
| [📘 **HOW_GA_ONLY_WORKS.md**](HOW_GA_ONLY_WORKS.md) | Non-coders | What the GA does, with the evolution analogy |
| [📘 **HOW_LEACH_ONLY_WORKS.md**](HOW_LEACH_ONLY_WORKS.md) | Non-coders | What LEACH does and why it's the standard baseline |
| [🔬 **SOLAR_GA_WSN_TECHNICAL_DEEP_DIVE.md**](SOLAR_GA_WSN_TECHNICAL_DEEP_DIVE.md) | Developers / researchers | All 9 formulas with code, GA mechanics, 12-step round, design decisions, optimisations |

---

## 🧠 Core Ideas in 60 Seconds

### Why pick CHs with a Genetic Algorithm?

LEACH picks cluster heads at random. We score every candidate team on:

| Weight | Component |
|---|---|
| **30%** | Coverage — does this team cover most sensors? |
| **25%** | Energy — do these nodes have full batteries? |
| **25%** | Solar — is the sun shining on them right now? |
| **20%** | Spread — are they geographically well-distributed? |

…then evolve the team across 50 generations using tournament selection, elitism, crossover, and adaptive mutation.

### Why a "multi-sink" relay layer?

The radio energy model says cost grows as **`d²`** below ~88 m and **`d⁴`** above. A CH 100 m from the base station pays *enormously* more than one 50 m away. Adding **MS-CH super-leaders** lets distant CHs hand off their bundles to a closer relay — saving a huge amount of battery.

### Why "solar-aware" not just "battery-aware"?

A half-empty sensor in **direct sunlight** is about to recharge. A fully charged sensor in **shade** is about to drain. Looking at *current solar harvest* alongside battery level is what makes this protocol's choices smarter than a battery-only heuristic.

---

## 🎛️ Configuration Options

All thresholds are tunable at runtime. Defaults shown:

| Parameter | Default | Range | Description |
|---|---|---|---|
| `FIELD` | 100 | 50–2000 | Field side length (m) |
| `NUM_NODES` | 50 | 10–5000 | Number of sensors |
| `NUM_ROUNDS` | 300 | 50–5000 | Simulation duration |
| `CH_PERCENT` | 10% | 2–30 | Target CH fraction (auto-scales) |
| `RELAYS_PER_MS` | 4 | 1–50 | Relay CHs per super-leader |
| `E_INITIAL` | 0.5 J | 0.01–10 | Starting battery |
| `MAX_HARVEST` | 0.002 J | 0.0–0.1 | Peak solar/round |
| `PACKET_SIZE` | 4000 bits | 100–100000 | Data packet size |
| `GA_POP` | 30 | 10–300 | GA population |
| `GA_GEN` | 50 | 10–500 | GA generations/round |
| `GA_MUT` | 0.10 | 0.0–1.0 | Base mutation rate |
| `GA_CX` | 0.80 | 0.0–1.0 | Crossover rate |
| `DIRECT_DIST` | 55 m | ≥10 | Max distance for direct CH→BS |
| `DIRECT_NRG` | 0.40 | 0.0–1.0 | Min battery for direct CH→BS |
| `SNAPSHOT_EVERY` | 50 | 0–10000 | Snapshot interval (0 = off) |

---

## 🔬 Implementation Highlights

- **First-Order Radio Model:** the same energy model used in the original LEACH paper, with the `d²` ↔ `d⁴` crossover at `d₀ ≈ 87.7 m`.
- **24-hour solar cycle:** half-sine wave from 06:00 to 18:00 with 5% per-node Gaussian noise.
- **Batched NumPy fitness:** evaluates the entire GA population in one tensor pass — about **60× faster** than per-chromosome Python loops.
- **k-Medoids spatial clustering:** for placing multiple MS-CHs across distinct relay zones with farthest-first seeding.
- **Adaptive mutation + early stopping:** mutation ramps up linearly when fitness plateaus, and the GA exits early once converged.
- **Memory-bounded fallback:** above 4M tensor elements (~32 MB), fitness evaluation switches to a per-chromosome loop to prevent swap on big networks.

For the full math and code, see [`SOLAR_GA_WSN_TECHNICAL_DEEP_DIVE.md`](SOLAR_GA_WSN_TECHNICAL_DEEP_DIVE.md).

---

## 📚 References

The protocol design is informed by:

1. **Heinzelman, W. R., Chandrakasan, A., & Balakrishnan, H.** *Energy-Efficient Communication Protocol for Wireless Microsensor Networks (LEACH).* HICSS, 2000.
2. **Muruganantham, N., & El-Ocla, H.** *Routing using Genetic Algorithm in Wireless Sensor Networks.* 2020.
3. **Wu et al.** *A Genetic Algorithm-Based Routing Protocol for Energy-Harvesting Wireless Sensor Networks.* IET, 2013.
4. *Genetic Algorithm-Based Energy Efficient Routing for WSNs.* ACSIJ, 2014.
5. *Routing Optimisation in IoT Using Genetic Algorithms.* 2023.

---

## 🤝 Contributing

Pull requests are welcome! Some ideas to explore:

- 🌐 Mobile sinks / unmanned-aerial-vehicle base stations
- 📡 Variable transmission power per node
- 🌧️ Stochastic solar harvest with weather noise
- 🧮 Compare against PEGASIS, HEED, or DEEC baselines
- 🐍 PyTorch port of the GA fitness for GPU acceleration

If you're filing an issue, please include the configuration parameters you used and the seed (default `42`) so the run is reproducible.

---

## 📄 License

MIT License

Copyright (c) 2026 Flute_Moon

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

<div align="center">

### 🌟 If this project helped your research, give it a star! 🌟

Made with care by [Imperial-Dragan](https://github.com/Flute-Moon/)

</div>
