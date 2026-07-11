# Version 1.1 Report — Solar-Aware GA Multi-Sink WSN Protocol (`ga_only_v1_1.py`)

**A deep, plain-language explanation of why `ga_only_v1_1.py` was built, what was wrong with the
original `ga_only.py`, and exactly what changed.**

---

## Table of contents

1. [Executive summary (read this first)](#1-executive-summary)
2. [What the program actually does](#2-what-the-program-actually-does)
3. [Why we developed v1.1 (the motivation)](#3-why-we-developed-v11-the-motivation)
4. [The six defects and their fixes — one by one](#4-the-six-defects-and-their-fixes)
5. [Old vs New — side-by-side comparison](#5-old-vs-new--side-by-side-comparison)
6. [How a single round works in v1.1 (end to end)](#6-how-a-single-round-works-in-v11)
7. [Results observed in the topology snapshots](#7-results-observed-in-the-topology-snapshots)
8. [How to run it](#8-how-to-run-it)
9. [Conclusion](#9-conclusion)

---

## 1. Executive summary

`ga_only.py` is a simulation of a **solar-powered wireless sensor network (WSN)** whose cluster
heads are chosen every round by a **Genetic Algorithm (GA)**. It works, but while reviewing it we
found **six concrete defects** — one of which produced *visibly wrong* topology pictures and another
that quietly **killed sensor nodes in one part of the field**.

`ga_only_v1_1.py` is a **corrected copy** of that file. The original is left untouched so the two can
be compared. All six fixes are labelled in the code with `[v1.1 Fix N]` comments.

**The headline outcome** (from the topology snapshots that were run):

| Metric (round 1050, 250-node network) | `ga_only.py` (old) | `ga_only_v1_1.py` (new) |
|---|---|---|
| Multi-sink tier | **"MS-SKIPPED"** + a fake/orphan MS-CH star | **"MS-USED", 2 real MS-CHs** |
| Dead sensor nodes | **19 dead** | **10 dead** (≈ 47 % fewer) |
| Cluster-head placement | crowded near the base station | spread across the whole field |
| Topology image | title contradicted the drawing | title and drawing agree |

In short: **v1.1 makes the protocol behave the way it was designed to, and the pictures finally tell
the truth.**

---

## 2. What the program actually does

Before the fixes make sense, here is the protocol in plain English.

### 2.1 The players

- **Sensor nodes** — small battery devices scattered on a square field. They sense data.
- **Base Station (BS)** — the sink where all data must eventually arrive. It never runs out of power.
- **Cluster Head (CH)** — a sensor *promoted* for one round to collect its neighbours' data.
- **Multi-Sink Cluster Head (MS-CH)** — a *super-collector* promoted from among the CHs that are far
  from the BS; it gathers data from several such CHs and makes one long transmission to the BS.

### 2.2 The 3-tier data flow

```
Tier 1:  Sensor  ──►  nearest CH
Tier 2:  CH      ──►  BS directly            (PATH A — if close + healthy battery)
              or ──►  an MS-CH               (PATH B — if far or low battery)
Tier 3:  MS-CH   ──►  BS                      (PATH C — one long transmission for the whole group)
```

The point of the MS-CH tier is **energy saving**: instead of many far-away CHs each making an
expensive long transmission to the BS, they hand their data to one MS-CH that transmits once.

### 2.3 Why a Genetic Algorithm?

Every round the network must decide **which sensors become CHs**. That is a hard combinatorial
choice. The GA searches for a good CH set by scoring candidate sets with a **fitness function** that
rewards four (originally five) things:

| Fitness term | Meaning | Weight (old → new) |
|---|---|---|
| `e_score` | CHs have high residual **energy** | 0.20 → 0.20 |
| `s_score` | CHs are **solar-healthy** (charging + charged) | 0.20 → 0.20 |
| `c_score` | CHs give good **coverage** of sensors | 0.30 → **0.35** |
| `sp_score` | CHs are **spread out** spatially | 0.15 → 0.15 |
| `bs_score` | at least one CH can reach the **BS** directly | 0.15 → **0.10** |

The energy model is the standard first-order radio model: transmitting over distance `d` costs
energy that grows with `d²` (and with `d⁴` beyond a crossover distance). **Long transmissions are
very expensive**, which is the whole reason the MS-CH tier exists.

### 2.4 The output

Every `SNAPSHOT_EVERY` rounds the program saves a **topology image** showing sensors, CHs, MS-CHs,
the BS, and the data paths (PATH A / B / C). The image title says either **"MS-USED"** (the MS-CH
tier was engaged) or **"MS-SKIPPED"** (every CH reached the BS directly).

---

## 3. Why we developed v1.1 (the motivation)

We did **not** create v1.1 to add features. We created it because the original `ga_only.py` had
**correctness bugs** that made it (a) behave against its own design and (b) draw misleading figures.
For a project or report, a figure that contradicts itself is a serious problem — it undermines trust
in every other result.

The two symptoms that forced the rewrite, both visible in the original snapshots:

1. **The multi-sink tier almost never worked, and when it "did" it was fake.**
   In the original runs, late-round snapshots were titled **"MS-SKIPPED (all CHs reach BS directly)"**
   yet still drew a green MS-CH star and a red arrow to the BS. The picture disagreed with its own
   title. The cause was a *single lonely relay CH being promoted to a pointless MS-CH* (details in
   Fix 1 and Fix 2 below).

2. **Sensors in the far part of the field were dying early.**
   The GA fitness had a term (`bs_score`) that rewarded putting **most** CHs near the base station.
   That pulled cluster heads into the top of the field, leaving sensors far from the BS with no
   nearby CH — they had to make long, expensive transmissions and **died first** (Fix 3 + Fix 4).

Alongside those two, we fixed three smaller correctness/maintainability issues (Fix 5, Fix 6) and one
that was purely cosmetic-but-misleading (Fix 2). Together these are the **"Tier-1" fixes** — the
must-do corrections, as opposed to optional enhancements.

**Guiding principle for v1.1:** *fix what is wrong, change nothing else.* The routing design, the
3-tier architecture, the GA mechanics, and the energy model are all identical to the original. Only
the buggy pieces were touched.

---

## 4. The six defects and their fixes

Each fix below shows the **problem in plain words**, the **old code**, the **new code**, and the
**impact**.

---

### Fix 1 — The "orphan MS-CH" (the most important bug)

**Problem.** An MS-CH is only useful if it collects data from *other* CHs. But the old code would
elect an MS-CH even when there was **only one** relay CH — so that single CH became an MS-CH with
**nobody to collect from**. It paid the extra cost of being an MS-CH for zero benefit, and it created
the fake green star that made the pictures wrong.

**Old code (`ga_only.py`):**
```python
def get_num_ms(num_relay_chs: int, cfg: dict) -> int:
    if num_relay_chs <= 0:          # only skips when there are ZERO relays
        return 0
    return max(1, min(num_relay_chs,
                      math.ceil(num_relay_chs / cfg["RELAYS_PER_MS"])))
```
So `1 relay CH → 1 MS-CH` (an orphan).

**New code (`ga_only_v1_1.py`):**
```python
def get_num_ms(num_relay_chs: int, cfg: dict) -> int:
    # [v1.1 Fix 1] need at least TWO relay CHs before electing an MS-CH
    if num_relay_chs <= 1:          # 0 OR 1 relay -> no MS-CH
        return 0
    return max(1, min(num_relay_chs,
                      math.ceil(num_relay_chs / cfg["RELAYS_PER_MS"])))
```

**Plus a safety net** in the round logic so the lone relay CH still delivers its data (it now
transmits **directly** to the BS instead of being silently dropped):
```python
# [v1.1 Fix 1] any relay CH left without an MS-CH sends directly to the BS
for ch in relay_chs:
    if ch.role == "CH" and ch.assigned_ms is None:
        ch.goes_direct = True
        direct_chs.append(ch)
```

**Impact.** No more meaningless MS-CHs. The multi-sink tier now only appears when it genuinely helps
(2+ relay CHs), and no data is ever lost.

> Behaviour of the fixed count (verified): `0 relays → 0`, `1 → 0`, `2 → 1`, `5 → 2`, `9 → 3`.

---

### Fix 2 — The topology image contradicted itself

**Problem.** The picture drew a green MS-CH star and a red "MS-CH → BS" arrow for **every** elected
MS-CH, even the orphan from Fix 1 — while the title logic decided "MS-SKIPPED". So you got a
**"MS-SKIPPED"** title *with a star and arrow on screen*.

**Old code** drew the star/arrow for all `ms_chs` unconditionally and computed:
```python
n_ms    = len(ms_chs)
ms_used = n_ms > 0 and any(c.assigned_ms is not None for c in relay_chs)
```

**New code** first works out which MS-CHs are *real* (have at least one follower), and only those get
drawn — and the title is driven by the same set:
```python
# [v1.1 Fix 2] only MS-CHs that actually have relay followers are "real"
served_ms_ids = {c.assigned_ms for c in relay_chs if c.assigned_ms is not None}
...
n_ms    = len(served_ms_ids)
ms_used = n_ms > 0
# star + red PATH-C arrow are gated on:  if m.id in served_ms_ids
```

**Impact.** The title and the drawing can never disagree again. "MS-USED (2 MS-CHs)" means exactly
two green stars with two red arrows.

---

### Fix 3 — `bs_score` was starving coverage on the far side of the field

**Problem.** The old `bs_score` rewarded the **fraction of CHs** sitting within `DIRECT_DIST` of the
base station. The GA therefore learned to cluster CHs near the BS to maximise that fraction —
abandoning sensors far from the BS.

**Old code:**
```python
# fraction of CHs within DIRECT_DIST of the BS  -> pulls CHs toward the BS
bs_score = (ch_bs_d <= cfg["DIRECT_DIST"]).sum(axis=1) / max(K, 1)

fitness = (0.20*e_score + 0.20*s_score
           + 0.30*c_score + 0.15*sp_score + 0.15*bs_score)
```

**New code:** reward only what PATH A truly needs — that **at least one** CH can reach the BS. If none
can, degrade gently by how close the nearest one is. Coverage weight is raised (0.30 → 0.35), the
`bs_score` weight is lowered (0.15 → 0.10):
```python
has_direct = (ch_bs_d <= cfg["DIRECT_DIST"]).any(axis=1)          # at least ONE CH near BS
closest    = 1.0 - np.minimum(ch_bs_d.min(axis=1) / max_dist, 1.0)
bs_score   = np.where(has_direct, 1.0, closest)

fitness = (0.20*e_score + 0.20*s_score
           + 0.35*c_score + 0.15*sp_score + 0.10*bs_score)
```

**Impact.** The GA no longer trades away coverage to hug the base station. CHs spread across the whole
field, so far-side sensors keep a nearby CH and stop dying early.

---

### Fix 4 — The default "direct-to-BS" distance was too large

**Problem.** `DIRECT_DIST` decides when a CH is "close enough" to skip the MS-CH tier and transmit
straight to the BS. The old default was **0.75 × field**, which is so large that *almost every* CH
qualified as "direct" — so the MS-CH tier (the whole novelty of the protocol) almost never ran.

**Old:** `d_dist = round(field * 0.75)`
**New:** `d_dist = round(field * 0.55)`

**Impact.** With a smaller threshold, CHs far from the BS become relay CHs → the MS-CH tier actually
engages. (This is a *default*; the user can still type any value at the prompt.)

---

### Fix 5 — Runs could not be varied for averaging

**Problem.** `run_simulation` hard-coded the random seed, so every run produced an identical result.
That makes proper **Monte-Carlo averaging** (running many seeds and averaging) impossible without
editing the code.

**Old:** `def run_simulation(cfg):` → internally `create_nodes(cfg, seed=42)`
**New:** `def run_simulation(cfg, seed=42):` → `create_nodes(cfg, seed=seed)`

**Impact.** The default (42) keeps runs reproducible, but you can now pass any seed — or `None` for a
fully random run — to average results over many trials.

---

### Fix 6 — Dead code (`max_dist` computed but never used)

**Problem.** The old `bs_score` block computed `max_dist = hypot(field, BS_Y)` and then never used it.

**Fix.** The reworked `bs_score` in Fix 3 uses `max_dist` to normalise the "closest CH" distance into
a clean 0–1 value. No more dead code.

---

## 5. Old vs New — side-by-side comparison

### 5.1 Code-level differences (the entire diff, summarised)

| Area | `ga_only.py` (old) | `ga_only_v1_1.py` (new) |
|---|---|---|
| MS-CH count rule | `relays ≤ 0 → 0` (allows orphan) | `relays ≤ 1 → 0` (no orphan) |
| Lone relay CH | could become a useless MS-CH | falls back to **direct BS**, never dropped |
| Fitness weights | `0.20/0.20/0.30/0.15/0.15` | `0.20/0.20/**0.35**/0.15/**0.10**` |
| `bs_score` meaning | fraction of CHs near BS (bad) | "≥1 CH near BS" else nearest-distance |
| `DIRECT_DIST` default | `0.75 × field` | `0.55 × field` |
| Seed control | hard-coded 42 in `run_simulation` | `seed` parameter (default 42) |
| `max_dist` | computed, unused | used to normalise `bs_score` |
| Snapshot MS visuals | drawn for **all** elected MS-CHs | drawn only for **real** MS-CHs (`served_ms_ids`) |
| Title vs drawing | could contradict | always consistent |

Everything else — the Node/energy model, GA operators (selection, crossover, mutation, elitism,
adaptive mutation, early stop), sensor assignment, k-medoids MS placement, re-election, and stats — is
**unchanged**.

### 5.2 Behavioural differences

| Behaviour | Old | New |
|---|---|---|
| When does the MS-CH tier appear? | rarely (big `DIRECT_DIST`), and sometimes fake | when 2+ CHs are far from BS |
| Where do CHs cluster? | near the base station | spread across the field |
| Which sensors die first? | far-from-BS sensors, early | deaths are fewer and more even |
| Do the figures match reality? | not always | yes |
| Can you run a Monte-Carlo study? | no (fixed seed) | yes (seed parameter) |

### 5.3 Results comparison (from the provided 250-node snapshots)

| Round | `ga_only.py` (old) | `ga_only_v1_1.py` (new) |
|---|---|---|
| 0 | (baseline) | MS-USED, 2 MS-CHs, 250/250 alive |
| 450 | **MS-SKIPPED**, 24 direct, **1 orphan MS-CH**, CHs crowded near BS | **MS-USED, 2 MS-CHs**, 250/250 alive, CHs spread |
| 1050 | MS-SKIPPED, 22 direct, orphan MS-CH, **231/250 alive (19 dead)** | **MS-USED, 2 MS-CHs**, **240/250 alive (10 dead)** |

> **Note on rigour:** these numbers come from the runs that were carried out while reviewing the
> code. For a publication-grade comparison, run **both** files with the **same configuration and the
> same seed** and compare the printed summary (first-node-death round, network lifetime, packets
> delivered, final residual energy, energy standard deviation). v1.1's Fix 5 makes that
> apples-to-apples comparison possible.

---

## 6. How a single round works in v1.1

This is the exact sequence inside `simulate_round_ga`, so you can follow the code:

1. **Solar harvest** — every alive node top-ups its battery based on the time-of-day sunlight curve
   and its own panel efficiency.
2. **Reset roles** — everyone becomes a plain sensor again for this round.
3. **Refresh world state** — build fast NumPy arrays of alive nodes; compute how many CHs to elect
   (`get_num_chs`, scales with alive count).
4. **GA elects the CH set** (`run_ga_ch_election`) using the 5-term fitness.
5. **Path decision** (`decide_ch_paths`) — each CH is labelled **direct** (close + healthy) or
   **relay** (far or low battery).
6. **MS-CH election** (`get_num_ms` + `elect_ms_chs`) — only if there are **2+ relay CHs**
   *(Fix 1)*. With multiple MS-CHs, relay CHs are grouped into zones by k-medoids and the best node
   per zone becomes that zone's MS-CH.
7. **Safety net** *(Fix 1)* — any relay CH still without an MS-CH is switched to **direct-to-BS** so
   its data is never lost.
8. **Sensors → nearest CH** (vectorised) and transmit.
9. **CHs aggregate and forward** — direct CHs send to the BS; relay CHs send to their MS-CH.
10. **MS-CH re-election** — if an MS-CH's battery falls below a threshold mid-round, a healthier peer
    takes over.
11. **MS-CHs transmit to the BS** (PATH C).
12. **Record stats** and, every `SNAPSHOT_EVERY` rounds, draw the topology image with the
    consistency fixes from Fix 2.

---

## 7. Results observed in the topology snapshots

Reading the images produced by the two versions:

- **Old (`ga_only.py`)** — at rounds 450 and 1050 the title read *"MS-SKIPPED (all CHs reach BS
  directly)"* while a lone green MS-CH star and a red arrow were still drawn (the orphan). Cluster
  heads were bunched toward the top of the field near the base station, and dead sensors (grey ×)
  piled up along the far edges. By round 1050, **19 nodes were dead**.

- **New (`ga_only_v1_1.py`)** — every snapshot correctly read *"MS-USED (2 MS-CHs)"* with exactly two
  green stars, each collecting a cluster of relay CHs (orange, PATH B) and forwarding once to the BS
  (red, PATH C). Cluster heads were spread across the whole field. By round 1050, only **10 nodes
  were dead**, and they were scattered rather than concentrated in the abandoned far region.

**Interpretation.** The fixes did two real things: (1) they switched the multi-sink tier back on and
made the picture honest, and (2) by removing the base-station bias they balanced energy use across the
field, which is why roughly **half as many nodes had died** by the same round.

---

## 8. How to run it

```bash
python3 ga_only_v1_1.py
```

You will be prompted for each parameter (press ENTER to accept the default in `[brackets]`). A good
mid-size run that clearly shows the MS-CH tier:

| Prompt | Suggested value |
|---|---|
| Field size (m) | 300 |
| Number of sensor nodes | 150 |
| Base station X / Y | 150 / 320 (defaults) |
| Rounds | 600 |
| CH percentage | 10 |
| Relay CHs per MS-CH | 3 |
| Initial energy (J) | 1.0 |
| Peak solar (J/round) | 0.004 |
| Max distance CH→BS direct | 150 |
| Save image every N rounds | 50 |

Outputs:
- `topology_snapshots/ga_round_XXXX.png` — per-round topology images
- `ga_results.png` — six summary graphs (lifetime, energy, deaths, balance, CH/MS counts, solar cycle)
- `ga_topology.png` — a labelled illustration of the three data paths
- A printed results summary (first death, lifetime, packets to BS, residual energy, etc.)

**Requirements:** Python 3 with `numpy` and `matplotlib` installed.

---

## 9. Conclusion

`ga_only_v1_1.py` is not a redesign — it is the **correct version** of `ga_only.py`. Six targeted
fixes remove an orphan-MS-CH bug, stop the topology figures from lying, and end the base-station bias
that was killing far-field sensors early. In the runs we compared, the multi-sink tier now engages as
intended and roughly **half as many nodes die** by the same round, with a more even energy spread
across the field.

For any demonstration or report of this solar-aware GA multi-sink protocol, **`ga_only_v1_1.py` is the
version to use**; keep `ga_only.py` only as the "before" reference when explaining what was fixed.

---

*Prepared as documentation for the `ga_only_v1_1.py` update. All code quotes were taken directly from
`ga_only.py` and `ga_only_v1_1.py` in this repository.*
