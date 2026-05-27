# How `leach_only.py` Works — A Plain English Guide

> A friendly explanation for people who don't write code.
> No programming knowledge needed!

---

## 1. The Big Picture (the same imaginary field)

Imagine the same scene as before: **50 tiny weather sensors** scattered across a football field, each with a small battery and a mini solar panel, all trying to send their readings to a **Base Station** at the edge of the field.

The problem is the same too: **radios drain batteries fast**, and shouting far costs much more than whispering close.

This file uses one of the **oldest and most famous** strategies for solving this problem. It's called **LEACH**, which stands for **"Low-Energy Adaptive Clustering Hierarchy"**. Researchers Heinzelman and colleagues invented it in the year 2000, and it's still the standard "baseline" that every new sensor-network idea is compared against.

Think of LEACH as the **"original recipe"**, and `ga_only.py` (which we explained earlier) as a **"smarter modern version"**.

---

## 2. The LEACH Strategy (just 2 layers)

LEACH organizes the sensors into a **simpler 2-layer structure** — there are no "super leaders" here:

```
  Base Station (the boss)
        ^
        |
    [ CH ]  <-- "team leader" (Cluster Head)
        ^
        |
  [sensor] [sensor] [sensor]  <-- regular workers
```

### Layer 1 — Workers (regular sensors)
Each worker takes a measurement and **whispers** it to the nearest team leader.

### Layer 2 — Team Leaders (CHs)
A team leader gathers all the whispers from its team, **bundles them into one message**, and **shouts it directly to the Base Station** — every time, no matter how far away the Base Station is.

That's it. There's no Path B. There are no super leaders. Every team leader makes its own long-distance shout.

This is **simpler** than the GA version, but also **wasteful**: a team leader sitting in the far corner of the field still has to shout all the way home, burning a lot of battery. That's why LEACH is the baseline — it works, but newer protocols try to do better.

---

## 3. How Are Team Leaders Chosen? — Just Roll the Dice

Here's the most important difference from `ga_only.py`:

> **LEACH picks the team leaders completely at random, every round.**

There's no evolution. No fitness scores. No looking at battery levels or sunshine. The program just shuffles the alive sensors and randomly picks 10% of them (5 out of 50, by default) to be team leaders for the next round.

Why does this work at all? Because of **fairness over time**. If you're randomly chosen each round, then **on average**, the burden of being a team leader is spread evenly across all sensors. No single sensor gets stuck doing all the heavy lifting forever — eventually the dice will pick someone else.

The downside: random picking sometimes chooses a sensor that's already nearly empty, or one stuck in a corner. That's wasteful. The GA version (`ga_only.py`) tries to fix that by *thinking* about who should be the leader. LEACH just trusts the dice.

---

## 4. What Happens in One "Round" of LEACH

A round is one heartbeat of the network. Here's the sequence:

1. **Sun rises/sets** — every alive sensor gets a small recharge if it's daytime.
2. **Reset roles** — yesterday's leaders go back to being regular workers.
3. **Random election** — the program rolls the dice and picks ~10% of alive sensors to be today's team leaders.
4. **Workers find their leader** — each worker is matched to its **nearest** team leader.
5. **Workers whisper** their reading to their leader. Each whisper costs a small amount of battery.
6. **Leaders bundle** the whispers into one packet (also costs a tiny bit of battery).
7. **Leaders shout** the bundle straight to the Base Station — no shortcuts, no relays.
8. **Record statistics** — how many sensors are still alive? How much energy is left?

The simulation runs **300 rounds by default**, or until everyone dies.

---

## 5. What's the Same as `ga_only.py`?

The two files share a lot of the underlying physics, so comparisons are fair:

- Same **field size**, same **number of sensors**, same **starting battery**.
- Same **radio energy formulas** (shouting far costs more than whispering close).
- Same **solar recharge model** (sine-wave day/night cycle).
- Same **packet size** and **measurement style**.
- Same **snapshot images** showing the field over time.

The **only real difference** is *how* team leaders are chosen and *whether* there's a super-leader layer.

| Feature | LEACH (this file) | GA (`ga_only.py`) |
|---|---|---|
| Layers | 2 (workers → leaders → boss) | 3 (workers → leaders → super-leaders → boss) |
| How leaders are picked | Random dice roll | Genetic Algorithm (evolution) |
| Solar awareness | None | Yes — picks sun-bathed leaders |
| Long-distance shouting | Every leader shouts to base | Far leaders relay through a super-leader |
| Complexity | Simple | More clever |

---

## 6. What You Get When You Run It

You answer the same kind of setup questions at startup (field size, number of nodes, etc.). Then:

- **Status updates** in the terminal showing alive count, total energy remaining, etc.
- **Snapshot images** every 50 rounds in a `topology_snapshots` folder. Each picture shows:
  - Light blue dots = alive workers
  - Grey X marks = dead sensors
  - Dark blue triangles = today's team leaders
  - A red square = the Base Station
  - Dashed blue arrows from every team leader straight to the Base Station (no relays!)
- **A results image** (`leach_results.png`) with 6 graphs:
  - Network lifetime (how many alive over time)
  - Total remaining energy over time
  - Cumulative deaths over time
  - Energy balance (are batteries depleting evenly or unevenly?)
  - How the leader count changes as sensors die
  - The day/night solar cycle
- **Final summary** with key metrics like "first node died at round X", "network died at round Y", and "total packets delivered".

---

## 7. Why Run LEACH at All?

You might wonder: *if the GA version is smarter, why even keep LEACH around?*

Three reasons:

1. **Benchmark.** When researchers invent a new protocol, they run LEACH on the same setup and show "look, our protocol lasted 30% longer than LEACH". You need a baseline to claim improvement.
2. **Simplicity.** LEACH is easy to understand, easy to implement on cheap hardware, and uses very little processing power on each sensor. Sometimes "good enough" is enough.
3. **Robustness.** Random picking means there's no single decision point that can fail. Even if half the network breaks, the dice keep rolling.

So LEACH plays the role of the **honest baseline** — the standard old recipe that any new idea (like the solar-aware GA approach) must beat to be considered useful.

---

## 8. Glossary (in case you got lost)

| Term | Meaning |
|---|---|
| **LEACH** | Low-Energy Adaptive Clustering Hierarchy — the classic baseline protocol |
| **Node / Sensor** | A small battery-powered device that takes measurements |
| **Base Station (BS)** | The central computer that collects all the data |
| **CH (Cluster Head)** | A "team leader" sensor that gathers data from neighbors |
| **Round** | One full cycle of the simulation |
| **Random election** | Choosing leaders by chance, not by scoring them |
| **Energy harvest** | Recharging the battery from the solar panel |
| **Packet** | A bundle of data sent over the radio |
| **Baseline** | The simple reference method that newer ideas must beat |

---

*That's the whole story. LEACH is the simple, classic, "throw the dice" approach. The GA version is the modern, "think it through" approach. Running both — which is what `solar_ga_wsn.py` does — lets you measure exactly how much the smarter strategy is worth.*
