"""
================================================================================
                    LEACH Baseline Protocol Runner
              for Wireless Sensor Assisted IoT Networks
                   ---  LEACH-ONLY  RUNNER  ---
================================================================================
  This file is the LEACH-only spin-off of `solar_ga_wsn`.
  Behaviour, energy model, solar harvest, and snapshot output are IDENTICAL
  to the LEACH branch of the original combined script. The GA / MS-CH stage
  has been removed so this script outputs only the LEACH-protocol results.

  LEACH (Low-Energy Adaptive Clustering Hierarchy):
    Tier 1 -> Sensor nodes : sense data, send to nearest CH
    Tier 2 -> Cluster Heads: aggregate sensor data and ship DIRECT to BS
    No MS-CH stage. Cluster heads are picked at random each round.

  Reference: Heinzelman et al. - LEACH protocol baseline
================================================================================
"""

import math
import os
import random
from dataclasses import dataclass, field as dc_field
from typing import List, Dict

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Headless-friendly: never block on a GUI, even if matplotlib is configured for one.
plt.switch_backend("Agg")

SNAPSHOT_DIR = "topology_snapshots"


# ==============================================================================
# SECTION 1 - USER INPUT
# ==============================================================================

def get_user_input() -> dict:
    """
    Collect simulation parameters. Press ENTER to accept the default.
    LEACH only needs network, energy, and CH-percentage settings.
    """
    print("\n" + "=" * 65)
    print("  LEACH WSN Protocol - Configuration")
    print("=" * 65)
    print("  Press ENTER to use default value shown in [brackets]\n")

    def ask(prompt, default, cast=float, vmin=None, vmax=None):
        while True:
            try:
                raw = input(f"  {prompt} [{default}]: ").strip()
                val = cast(raw) if raw else default
                if vmin is not None and val < vmin:
                    print(f"    !  Must be >= {vmin}")
                    continue
                if vmax is not None and val > vmax:
                    print(f"    !  Must be <= {vmax}")
                    continue
                return val
            except ValueError:
                print(f"    !  Invalid - expected {cast.__name__}")

    print("  -- Network Setup --")
    field    = ask("Field size in metres (square)",        100, int,   50, 2000)
    n_nodes  = ask("Number of sensor nodes",                50, int,   10, 5000)
    bs_x     = ask("Base station X position (metres)",  field // 2, float, 0)
    bs_y     = ask("Base station Y position (metres)",  field + 20, float, 0)
    n_rounds = ask("Number of simulation rounds",           300, int,   50, 5000)

    print("\n  -- CH Percentage (scales with alive nodes) --")
    ch_pct   = ask("CH percentage of alive nodes (e.g. 10 = 10%)",
                   10, float, 2, 30)

    print("\n  -- Energy Settings --")
    e_init   = ask("Initial node energy (Joules)",          0.5, float, 0.01, 10.0)
    e_solar  = ask("Peak solar harvest rate (J/round)",   0.002, float, 0.0,   0.1)
    pkt      = ask("Packet size (bits)",                   4000, int,   100, 100000)

    print("\n  -- Topology Snapshots --")
    snap_every = ask("Save topology image every N rounds (0 = off)",
                     50, int, 0, 10000)

    print("\n  -- Validation --")
    init_chs = max(1, round(n_nodes * ch_pct / 100))
    print(f"  v  Initial CH count     : {init_chs}  "
          f"(= {n_nodes} nodes x {ch_pct}%)")
    print(f"  v  CH count auto-scales every round")
    if bs_y > field * 2:
        print("  !  Warning: BS is very far - high energy cost")
    print("  v  Configuration accepted\n")

    return {
        "FIELD"        : field,
        "NUM_NODES"    : n_nodes,
        "BS_X"         : bs_x,
        "BS_Y"         : bs_y,
        "NUM_ROUNDS"   : n_rounds,
        "CH_PERCENT"   : ch_pct / 100.0,
        "E_INITIAL"    : e_init,
        "MAX_HARVEST"  : e_solar,
        "PACKET_SIZE"  : pkt,
        "SNAPSHOT_EVERY": snap_every,
    }


def get_num_chs(alive_count: int, cfg: dict) -> int:
    """Dynamic CH count - recalculated every round."""
    if alive_count <= 0:
        return 0
    return max(1, min(alive_count, round(alive_count * cfg["CH_PERCENT"])))


# ==============================================================================
# SECTION 2 - RADIO & ENERGY CONSTANTS
# ==============================================================================

E_ELEC         = 50e-9
E_AMP          = 100e-12
E_MP           = 0.0013e-12
E_DA           = 5e-9
BATTERY_MAX    = 2.0
COMM_RANGE_PCT = 0.4
D0             = math.sqrt(E_AMP / E_MP)


# ==============================================================================
# SECTION 3 - NODE
# ==============================================================================

class Node:
    __slots__ = ("id", "x", "y", "energy", "alive", "role",
                 "assigned_ch", "assigned_ms", "goes_direct",
                 "packets_sent", "_cfg", "_dist_bs")

    def __init__(self, node_id: int, x: float, y: float, cfg: dict):
        self.id           = node_id
        self.x            = x
        self.y            = y
        self.energy       = cfg["E_INITIAL"]
        self.alive        = True
        self.role         = "sensor"
        self.assigned_ch  = None
        self.assigned_ms  = None
        self.goes_direct  = False
        self.packets_sent = 0
        self._cfg         = cfg
        self._dist_bs     = math.hypot(cfg["BS_X"] - x, cfg["BS_Y"] - y)

    def distance_to(self, x: float, y: float) -> float:
        return math.hypot(self.x - x, self.y - y)

    @property
    def distance_to_bs(self) -> float:
        return self._dist_bs

    def _tx_cost(self, bits: int, d: float) -> float:
        if d <= D0:
            return E_ELEC * bits + E_AMP * bits * d * d
        d2 = d * d
        return E_ELEC * bits + E_MP * bits * d2 * d2

    def _rx_cost(self, bits: int) -> float:
        return E_ELEC * bits

    def _agg_cost(self, bits: int, n: int) -> float:
        return E_DA * bits * n

    def transmit(self, to_x: float, to_y: float) -> bool:
        cost = self._tx_cost(self._cfg["PACKET_SIZE"],
                             math.hypot(self.x - to_x, self.y - to_y))
        self.energy       -= cost
        self.packets_sent += 1
        if self.energy <= 0:
            self.energy = 0
            self.alive  = False
        return self.alive

    def receive(self) -> bool:
        self.energy -= self._rx_cost(self._cfg["PACKET_SIZE"])
        if self.energy <= 0:
            self.energy = 0
            self.alive  = False
        return self.alive

    def aggregate(self, n_packets: int) -> bool:
        self.energy -= self._agg_cost(self._cfg["PACKET_SIZE"], n_packets)
        if self.energy <= 0:
            self.energy = 0
            self.alive  = False
        return self.alive

    def harvest_solar(self, solar_rate_now: float) -> None:
        if solar_rate_now <= 0:
            return
        harvest = max(0.0, solar_rate_now + random.gauss(0, solar_rate_now * 0.05))
        self.energy = min(self.energy + harvest, BATTERY_MAX)

    def reset_role(self) -> None:
        self.role        = "sensor"
        self.assigned_ch = None
        self.assigned_ms = None
        self.goes_direct = False

    @property
    def energy_fraction(self) -> float:
        return self.energy / self._cfg["E_INITIAL"]

    def __repr__(self) -> str:
        return (f"Node({self.id}, {self.role}, "
                f"{self.energy:.4f}J, alive={self.alive})")


def solar_rate_for_round(round_num: int, max_harvest: float) -> float:
    hour = round_num % 24
    return max_harvest * max(0.0, math.sin(math.pi * hour / 12))


# ==============================================================================
# SECTION 4 - WORLD STATE
# ==============================================================================

@dataclass
class World:
    nodes: List[Node]
    alive_idx:  np.ndarray = dc_field(default_factory=lambda: np.empty(0, dtype=np.int32))
    alive_xy:   np.ndarray = dc_field(default_factory=lambda: np.empty((0, 2)))
    alive_e:    np.ndarray = dc_field(default_factory=lambda: np.empty(0))
    alive_dbs:  np.ndarray = dc_field(default_factory=lambda: np.empty(0))
    id_to_idx:  Dict[int, int] = dc_field(default_factory=dict)

    def refresh(self) -> None:
        alive = [n for n in self.nodes if n.alive]
        if not alive:
            self.alive_idx  = np.empty(0, dtype=np.int32)
            self.alive_xy   = np.empty((0, 2))
            self.alive_e    = np.empty(0)
            self.alive_dbs  = np.empty(0)
            self.id_to_idx  = {}
            return
        self.alive_idx = np.fromiter((n.id for n in alive), dtype=np.int32,
                                     count=len(alive))
        self.alive_xy  = np.array([(n.x, n.y) for n in alive], dtype=np.float64)
        self.alive_e   = np.fromiter((n.energy for n in alive),
                                     dtype=np.float64, count=len(alive))
        self.alive_dbs = np.fromiter((n._dist_bs for n in alive),
                                     dtype=np.float64, count=len(alive))
        self.id_to_idx = {int(nid): i for i, nid in enumerate(self.alive_idx)}


def vectorized_assign(sensor_xy: np.ndarray, ch_xy: np.ndarray) -> np.ndarray:
    if ch_xy.shape[0] == 0 or sensor_xy.shape[0] == 0:
        return np.empty(sensor_xy.shape[0], dtype=np.int64)
    diff = sensor_xy[:, None, :] - ch_xy[None, :, :]
    d2   = np.einsum("ijk,ijk->ij", diff, diff)
    return d2.argmin(axis=1)


# ==============================================================================
# SECTION 5 - LEACH PROTOCOL ROUND
# ==============================================================================

def simulate_round_leach(nodes: List[Node],
                         world: World,
                         round_num: int,
                         cfg: dict,
                         stats: dict) -> bool:
    """
    LEACH - same solar model and dynamic CH count as the original.
    No MS-CH; every CH ships direct to BS.
    """
    solar_now = solar_rate_for_round(round_num, cfg["MAX_HARVEST"])
    if solar_now > 0:
        for n in nodes:
            if n.alive:
                n.harvest_solar(solar_now)
    for n in nodes:
        if n.alive:
            n.reset_role()

    world.refresh()
    alive_count = world.alive_idx.size
    num_chs = get_num_chs(alive_count, cfg)

    if alive_count < num_chs + 1:
        _record_stats(nodes, stats)
        stats["ch_counts"].append(0)
        return False

    elected_ids = random.sample(world.alive_idx.tolist(),
                                min(num_chs, alive_count))
    elected = [nodes[i] for i in elected_ids]
    for n in elected:
        n.role = "CH"

    ch_xy = np.array([(c.x, c.y) for c in elected], dtype=np.float64)
    ch_id_arr = np.array([c.id for c in elected], dtype=np.int64)
    ch_id_set = set(elected_ids)
    sensor_mask = np.array([nid not in ch_id_set
                            for nid in world.alive_idx], dtype=bool)
    sensor_xy  = world.alive_xy[sensor_mask]
    sensor_ids = world.alive_idx[sensor_mask]
    if sensor_xy.shape[0] > 0:
        assign_idx = vectorized_assign(sensor_xy, ch_xy)
        for sid, ai in zip(sensor_ids.tolist(), assign_idx.tolist()):
            nodes[sid].assigned_ch = int(ch_id_arr[ai])

    for nid in world.alive_idx.tolist():
        n = nodes[nid]
        if n.role == "sensor" and n.assigned_ch is not None:
            ch = nodes[n.assigned_ch]
            if ch.alive:
                n.transmit(ch.x, ch.y)
                ch.receive()

    member_count = {c.id: 0 for c in elected}
    for nid in world.alive_idx.tolist():
        n = nodes[nid]
        if n.role == "sensor" and n.assigned_ch in member_count:
            member_count[n.assigned_ch] += 1

    for ch in elected:
        if not ch.alive:
            continue
        ch.aggregate(member_count[ch.id])
        if ch.alive:
            ch.transmit(cfg["BS_X"], cfg["BS_Y"])
            stats["packets_to_bs"] += 1

    _record_stats(nodes, stats)
    stats["ch_counts"].append(num_chs)

    snap = cfg.get("SNAPSHOT_EVERY", 0)
    if snap and round_num % snap == 0:
        try:
            plot_topology_snapshot(nodes, elected, round_num, cfg)
        except Exception as e:
            print(f"  !  Snapshot failed at round {round_num}: {e}")
    return any(n.alive for n in nodes)


# ==============================================================================
# SECTION 6 - STATS
# ==============================================================================

def make_stats() -> dict:
    return {
        "alive_nodes"   : [],
        "dead_nodes"    : [],
        "total_energy"  : [],
        "energy_stddev" : [],
        "ch_counts"     : [],
        "packets_to_bs" : 0,
    }


def _record_stats(nodes: List[Node], stats: dict) -> None:
    energies = [n.energy for n in nodes if n.alive]
    alive = len(energies)
    stats["alive_nodes"].append(alive)
    stats["dead_nodes"].append(len(nodes) - alive)
    stats["total_energy"].append(sum(energies))
    stats["energy_stddev"].append(float(np.std(energies)) if energies else 0.0)


# ==============================================================================
# SECTION 7 - SIMULATION RUNNER
# ==============================================================================

def create_nodes(cfg: dict) -> List[Node]:
    random.seed(42)
    np.random.seed(42)
    return [Node(i,
                 random.uniform(0, cfg["FIELD"]),
                 random.uniform(0, cfg["FIELD"]),
                 cfg)
            for i in range(cfg["NUM_NODES"])]


def run_simulation(cfg: dict):
    nodes = create_nodes(cfg)
    world = World(nodes=nodes)
    stats = make_stats()
    init_chs = max(1, round(cfg["NUM_NODES"] * cfg["CH_PERCENT"]))
    print(f"\n{'=' * 58}")
    print(f"  Protocol  : LEACH (baseline)")
    print(f"  Nodes     : {cfg['NUM_NODES']}   "
          f"Field : {cfg['FIELD']}x{cfg['FIELD']}m")
    print(f"  Rounds    : {cfg['NUM_ROUNDS']}  "
          f"Initial CHs: {init_chs} "
          f"({cfg['CH_PERCENT'] * 100:.0f}% - dynamic)")
    if cfg.get("SNAPSHOT_EVERY", 0):
        print(f"  Snapshots : every {cfg['SNAPSHOT_EVERY']} rounds -> "
              f"./{SNAPSHOT_DIR}/")
    print(f"{'=' * 58}")

    first_dead   = None
    network_dead = cfg["NUM_ROUNDS"]

    for r in range(cfg["NUM_ROUNDS"]):
        alive = simulate_round_leach(nodes, world, r, cfg, stats)

        dead_now = cfg["NUM_NODES"] - sum(1 for n in nodes if n.alive)
        if first_dead is None and dead_now >= 1:
            first_dead = r
            print(f"  *  First node died   : Round {r}")

        if not alive:
            network_dead = r
            print(f"  X  Network dead      : Round {r}")
            break

        step = max(cfg["NUM_ROUNDS"] // 5, 1)
        if r % step == 0:
            a = stats["alive_nodes"][-1]
            e = stats["total_energy"][-1]
            nchs = stats["ch_counts"][-1] if stats["ch_counts"] else "?"
            print(f"  Round {r:4d} | Alive: {a:3d}/{cfg['NUM_NODES']} "
                  f"| CHs: {nchs} | Energy: {e:.4f} J")

    if network_dead == cfg["NUM_ROUNDS"]:
        print(f"  v  Network survived all {cfg['NUM_ROUNDS']} rounds!")
    print(f"  Packets to BS     : {stats['packets_to_bs']}")
    print(f"{'=' * 58}")

    return stats, first_dead, network_dead, nodes


# ==============================================================================
# SECTION 8 - PLOTS
# ==============================================================================

def plot_results(leach_stats, leach_fd, cfg) -> None:
    """5 graphs: lifetime, energy, deaths, balance, dynamic CH, solar."""
    fig, axes = plt.subplots(2, 3, figsize=(17, 10))
    fig.suptitle(
        "LEACH Baseline Protocol\n"
        f"(Nodes={cfg['NUM_NODES']}, Field={cfg['FIELD']}m, "
        f"Rounds={cfg['NUM_ROUNDS']}, "
        f"CH%={cfg['CH_PERCENT'] * 100:.0f}% dynamic)",
        fontsize=12, fontweight="bold")

    C_LEACH = "#C0392B"
    rl = range(len(leach_stats["alive_nodes"]))

    # 1. Alive
    ax = axes[0, 0]
    ax.plot(rl, leach_stats["alive_nodes"], color=C_LEACH, lw=2, label="LEACH")
    if leach_fd:
        ax.axvline(leach_fd, color=C_LEACH, ls=":", alpha=0.6,
                   label=f"LEACH 1st death r{leach_fd}")
    ax.set(xlabel="Round", ylabel="Alive nodes",
           title="Network Lifetime",
           ylim=(0, cfg["NUM_NODES"] + 2))
    ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

    # 2. Total residual energy
    ax = axes[0, 1]
    ax.plot(rl, leach_stats["total_energy"], color=C_LEACH, lw=2, label="LEACH")
    ax.set(xlabel="Round", ylabel="Total residual energy (J)",
           title="Total Residual Energy")
    ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

    # 3. Dead nodes
    ax = axes[0, 2]
    ax.plot(rl, leach_stats["dead_nodes"], color=C_LEACH, lw=2, label="LEACH")
    ax.set(xlabel="Round", ylabel="Cumulative dead nodes",
           title="Node Deaths Over Time")
    ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

    # 4. Energy balance
    ax = axes[1, 0]
    ax.plot(rl, leach_stats["energy_stddev"], color=C_LEACH, lw=2, label="LEACH")
    ax.set(xlabel="Round", ylabel="Std deviation of energy (J)",
           title="Energy Balance\n(lower = more balanced)")
    ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

    # 5. Dynamic CH counts
    ax = axes[1, 1]
    if leach_stats["ch_counts"]:
        ax.plot(range(len(leach_stats["ch_counts"])),
                leach_stats["ch_counts"], color=C_LEACH, lw=2,
                label="LEACH CHs")
    ax.set(xlabel="Round", ylabel="Count",
           title="Dynamic CH Counts\n(scales with alive nodes)")
    ax.legend(fontsize=8); ax.grid(True, alpha=0.3)

    # 6. Solar harvest cycle
    ax = axes[1, 2]
    hours   = np.linspace(0, 48, 500)
    harvest = [cfg["MAX_HARVEST"] * max(0, math.sin(math.pi * (h % 24) / 12))
               for h in hours]
    ax.fill_between(hours, harvest, alpha=0.25, color="orange")
    ax.plot(hours, harvest, color="darkorange", lw=2)
    ax.set_xticks(range(0, 49, 6))
    ax.set_xticklabels([f"{h % 24:02d}:00" for h in range(0, 49, 6)])
    ax.set(xlabel="Hour of day", ylabel="Harvest rate (J/round)",
           title="Solar Harvest Model")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("leach_results.png", dpi=150, bbox_inches="tight")
    print("  Plot saved -> leach_results.png")
    plt.close()


def plot_topology_snapshot(nodes: List["Node"],
                           ch_nodes: List["Node"],
                           round_num: int,
                           cfg: dict) -> None:
    """LEACH snapshot - every CH ships direct to BS, no MS-CH stage."""
    F, BSX, BSY = cfg["FIELD"], cfg["BS_X"], cfg["BS_Y"]
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)

    alive_sensors_x: List[float] = []
    alive_sensors_y: List[float] = []
    dead_x: List[float] = []
    dead_y: List[float] = []
    sensor_to_ch: Dict[int, int] = {}
    for n in nodes:
        if not n.alive:
            dead_x.append(n.x)
            dead_y.append(n.y)
            continue
        if n.role == "sensor":
            alive_sensors_x.append(n.x)
            alive_sensors_y.append(n.y)
            if n.assigned_ch is not None:
                sensor_to_ch[n.id] = n.assigned_ch

    n_alive = sum(1 for n in nodes if n.alive)

    fig, ax = plt.subplots(figsize=(11, 11))
    ax.set_facecolor("#f4f6f9")
    ax.set_xlim(-8, F + 8)
    ax.set_ylim(-8, max(BSY + 20, F + 20))

    comm_range = F * COMM_RANGE_PCT
    for c in ch_nodes:
        ax.add_patch(plt.Circle((c.x, c.y), comm_range,
                                color="gray", fill=False,
                                alpha=0.08, lw=0.7, ls="--"))

    # Sensor -> CH lines (faint)
    for sid, cid in sensor_to_ch.items():
        s, c = nodes[sid], nodes[cid]
        if c.alive:
            ax.plot([s.x, c.x], [s.y, c.y],
                    color="#AABCD4", lw=0.45, alpha=0.40, zorder=1)

    # In LEACH every CH ships direct to BS
    for c in ch_nodes:
        if c.alive:
            ax.annotate("", xy=(BSX, BSY), xytext=(c.x, c.y),
                        arrowprops=dict(arrowstyle="->", color="#1A5FAD",
                                        lw=1.4, linestyle="dashed",
                                        alpha=0.7),
                        zorder=4)

    if alive_sensors_x:
        ax.scatter(alive_sensors_x, alive_sensors_y,
                   c="#7FB3D3", s=32, zorder=3, alpha=0.85,
                   edgecolors="white", lw=0.5)
    if dead_x:
        ax.scatter(dead_x, dead_y, c="#888", s=22, marker="x",
                   zorder=3, alpha=0.6, lw=1.0)

    for c in ch_nodes:
        if c.alive:
            ax.scatter(c.x, c.y, c="#1A5FAD", s=170, marker="^",
                       zorder=5, edgecolors="white", lw=1.2)

    ax.scatter(BSX, BSY, c="#C0392B", s=420, marker="s",
               zorder=7, edgecolors="darkred", lw=2)
    ax.text(BSX + 7, BSY + 3, "BS",
            fontsize=10, fontweight="bold", color="darkred")

    ax.add_patch(plt.Rectangle((0, 0), F, F, fill=False,
                               edgecolor="#999", lw=1.2, ls="--", alpha=0.5))

    ax.set_title(
        f"LEACH  Round {round_num:4d}   |   LEACH baseline (no MS-CH)\n"
        f"Alive: {n_alive}/{cfg['NUM_NODES']}   "
        f"CHs: {len(ch_nodes)}",
        fontsize=12, fontweight="bold", color="#C0392B", pad=12)

    handles = [
        mpatches.Patch(color="#7FB3D3", label="Sensor (alive)"),
        mpatches.Patch(color="#888",    label="Sensor (dead)"),
        mpatches.Patch(color="#1A5FAD", label="CH -> BS direct"),
        mpatches.Patch(color="#C0392B", label="Base Station"),
    ]
    ax.legend(handles=handles, loc="lower right",
              fontsize=8, framealpha=0.93, edgecolor="gray")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.grid(True, alpha=0.18)

    fname = os.path.join(SNAPSHOT_DIR,
                         f"leach_round_{round_num:04d}.png")
    plt.tight_layout()
    plt.savefig(fname, dpi=120, bbox_inches="tight")
    plt.close(fig)


# ==============================================================================
# SECTION 9 - SUMMARY
# ==============================================================================

def print_summary(leach_s, leach_fd, leach_nd, cfg) -> None:
    print("\n" + "=" * 64)
    print("  LEACH SIMULATION RESULTS SUMMARY")
    print("=" * 64)
    print(f"  {'Metric':<40} {'LEACH':>10}")
    print(f"  {'-' * 50}")

    def fmt(v):
        return str(v) if v else f">{cfg['NUM_ROUNDS']}"

    rows = [
        ("First node death (round)",      fmt(leach_fd)),
        ("Network lifetime (rounds)",     str(leach_nd)),
        ("Packets delivered to BS",       str(leach_s["packets_to_bs"])),
        ("Final residual energy (J)",
         f"{leach_s['total_energy'][-1]:.4f}" if leach_s["total_energy"] else "0"),
        ("Final energy std dev (J)",
         f"{leach_s['energy_stddev'][-1]:.4f}" if leach_s["energy_stddev"] else "0"),
        ("Avg CHs / round",
         f"{np.mean(leach_s['ch_counts']):.1f}" if leach_s['ch_counts'] else "0"),
        ("CH% used", f"{cfg['CH_PERCENT'] * 100:.0f}% dynamic"),
    ]
    for label, leach_val in rows:
        print(f"  {label:<40} {leach_val:>10}")
    print("=" * 64)


# ==============================================================================
# MAIN
# ==============================================================================

def main():
    print("\n" + "#" * 65)
    print("  LEACH Baseline Protocol")
    print("  for Wireless Sensor Assisted IoT  --  LEACH-ONLY RUNNER")
    print("#" * 65)

    cfg = get_user_input()

    leach_stats, leach_fd, leach_nd, _ = run_simulation(cfg)

    print_summary(leach_stats, leach_fd, leach_nd, cfg)

    print("\n  Generating plots...")
    plot_results(leach_stats, leach_fd, cfg)

    print("\n  All outputs saved.  Done.\n")


if __name__ == "__main__":
    main()
