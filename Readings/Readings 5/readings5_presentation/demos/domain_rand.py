"""
domain_rand.py - Slide 3 demo (Gurram et al., 2024 survey): domain randomization.

*** TOY MODEL - a 1-D push-cart, not a legged robot. ***
A cart must move 1 m and stop inside a +/-5 cm window. The floor friction, the
cart mass and the motor strength can all change, like a robot dog walking from
a dry floor onto a wet stain or a carpet.

The controller is a PD law with a friction-compensation term:
    force = strength * clip(kp*e - kd*v + ff*tanh(e/0.01), +/-F_max)
Its three gains are found by a quick random search (no long RL run):
  * FIXED controller:      tuned on ONE nominal floor (fastest success)
  * RANDOMIZED controller: tuned across many randomized floors (most successes)
Both are then tested on shifted floors and the success rates are compared.
Everything is vectorised with numpy, so the whole demo runs in about a second.
"""
import time

import numpy as np

import config
from demos.style import plt, toy_label

G = 9.81


# ----------------------------------------------------------------------------
# Simulation
# ----------------------------------------------------------------------------
def sample_envs(ranges, n, rng):
    """Draw n environments uniformly from {'friction': (lo, hi), ...}."""
    return {k: rng.uniform(lo, hi, size=n) for k, (lo, hi) in ranges.items()}


def simulate(gains, envs, return_traj=False):
    """Simulate every (controller, environment) pair at once.

    gains: array (C, 3) of [kp, kd, ff]
    envs:  dict of arrays, each shape (E,)
    Returns success (C, E) and settle time (C, E); optionally x(t).
    """
    dt = config.DR_DT
    steps = int(config.DR_HORIZON_S / dt)
    hold = int(config.DR_HOLD_S / dt)
    kp, kd, ff = (gains[:, i:i + 1] for i in range(3))          # (C, 1)
    mu = envs["friction"][None, :]                                # (1, E)
    m = envs["mass"][None, :]
    s = envs["strength"][None, :]
    C, E = gains.shape[0], mu.shape[1]

    x = np.zeros((C, E))
    v = np.zeros((C, E))
    x_meas, v_meas = x.copy(), v.copy()     # one-step sensor latency
    fric = mu * m * G
    inside = np.zeros((steps, C, E), dtype=bool)
    traj = np.zeros((steps, C, E)) if return_traj else None

    for k in range(steps):
        e = config.DR_GOAL - x_meas
        u = kp * e - kd * v_meas + ff * np.tanh(e / 0.01)
        force = s * np.clip(u, -config.DR_FORCE_LIMIT, config.DR_FORCE_LIMIT)
        x_meas, v_meas = x.copy(), v.copy()

        # Coulomb friction: stick when slow and the push is too weak
        moving = np.abs(v) > 1e-6
        v_moving = v + dt * (force - fric * np.sign(v)) / m
        stops = moving & (np.sign(v_moving) != np.sign(v)) & (np.abs(force) < fric)
        breakaway = (~moving) & (np.abs(force) > fric)
        v_static = np.where(breakaway, dt * (force - fric * np.sign(force)) / m, 0.0)
        v = np.where(moving, np.where(stops, 0.0, v_moving), v_static)
        x = x + dt * v

        inside[k] = (np.abs(config.DR_GOAL - x) < config.DR_POS_TOL) & (np.abs(v) < config.DR_VEL_TOL)
        if return_traj:
            traj[k] = x

    success = inside[-hold:].all(axis=0)
    # settle time = first step after which the cart stays inside the window
    outside_rev = ~inside[::-1]
    last_out = steps - np.argmax(outside_rev, axis=0)     # index after last "outside"
    last_out = np.where(outside_rev.any(axis=0), last_out, 0)
    settle = np.where(success, last_out * dt, np.inf)
    if return_traj:
        return success, settle, traj
    return success, settle


# ----------------------------------------------------------------------------
# Quick policy search (random search over the three gains)
# ----------------------------------------------------------------------------
def candidate_gains(rng, n):
    kp = 10 ** rng.uniform(np.log10(2), np.log10(150), n)
    kd = 10 ** rng.uniform(np.log10(0.3), np.log10(30), n)
    ff = rng.uniform(0.0, 5.0, n)
    return np.stack([kp, kd, ff], axis=1)


def tune_fixed(cands):
    """Tune on the single nominal floor: pick the FASTEST controller that succeeds."""
    nominal = {k: np.array([v]) for k, v in config.DR_NOMINAL.items()}
    success, settle = simulate(cands, nominal)
    return cands[int(np.argmin(settle[:, 0]))]


def tune_randomized(cands, rng):
    """Tune across randomized floors: pick the controller with the most
    successes (ties broken by mean settle time)."""
    envs = sample_envs(config.DR_RANDOM_RANGES, config.DR_N_TRAIN_ENVS, rng)
    success, settle = simulate(cands, envs)
    rate = success.mean(axis=1)
    mean_t = np.where(success, settle, config.DR_HORIZON_S).mean(axis=1)
    score = rate - 0.01 * mean_t
    return cands[int(np.argmax(score))]


def tune_both(seed=config.RANDOM_SEED):
    rng = np.random.default_rng(seed)
    cands = candidate_gains(rng, config.DR_N_CANDIDATES)
    return {"Fixed (tuned on one floor)": tune_fixed(cands),
            "Randomized (tuned on many floors)": tune_randomized(cands, rng)}


def evaluate(controllers, seed=config.RANDOM_SEED + 100):
    """Success rate of each controller on each shifted test condition."""
    rng = np.random.default_rng(seed)
    gains = np.stack(list(controllers.values()))
    results = {name: {} for name in controllers}
    for cond, ranges in config.DR_TEST_CONDITIONS.items():
        envs = sample_envs(ranges, config.DR_N_TEST_ENVS, rng)
        success, _ = simulate(gains, envs)
        for i, name in enumerate(controllers):
            results[name][cond] = float(success[i].mean())
    return results


# ----------------------------------------------------------------------------
# Figures
# ----------------------------------------------------------------------------
CTRL_COLORS = [config.GREY, config.ACCENT_2]


def success_bar_figure(results):
    conds = list(config.DR_TEST_CONDITIONS)
    fig, ax = plt.subplots(figsize=(12, 4.8))
    width = 0.38
    xs = np.arange(len(conds))
    for i, (name, rates) in enumerate(results.items()):
        vals = [100 * rates[c] for c in conds]
        bars = ax.bar(xs + (i - 0.5) * width, vals, width, label=name, color=CTRL_COLORS[i])
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.0f}%", ha="center",
                    fontsize=11, fontweight="bold")
    ax.set_xticks(xs, [c.replace(" (", "\n(") for c in conds])
    ax.set_ylabel("success rate (%)")
    ax.set_ylim(0, 118)
    ax.set_title(f"Success on shifted floors ({config.DR_N_TEST_ENVS} test episodes per condition)")
    ax.legend(loc="upper left", ncol=2)
    ax.grid(axis="x", visible=False)
    toy_label(ax, "TOY MODEL - 1-D push-cart, simulated")
    return fig


def live_figure(controllers, friction, mass, strength):
    """Run both controllers on the audience's slider setting."""
    env = {"friction": np.array([friction]), "mass": np.array([mass]),
           "strength": np.array([strength])}
    gains = np.stack(list(controllers.values()))
    success, settle, traj = simulate(gains, env, return_traj=True)
    t = np.arange(traj.shape[0]) * config.DR_DT
    fig, ax = plt.subplots(figsize=(12, 4.3))
    ax.axhspan(config.DR_GOAL - config.DR_POS_TOL, config.DR_GOAL + config.DR_POS_TOL,
               color=config.ACCENT, alpha=0.18, label="goal window (±5 cm)")
    outcome = {}
    for i, name in enumerate(controllers):
        ok = bool(success[i, 0])
        outcome[name] = ok
        ax.plot(t, traj[:, i, 0], lw=2.6, color=CTRL_COLORS[i],
                label=f"{name}: {'SUCCESS' if ok else 'FAIL'}")
    ax.set_xlabel("time (s)")
    ax.set_ylabel("cart position (m)")
    ax.set_title(f"Your floor: friction μ = {friction:.2f}, mass = {mass:.1f} kg, motor strength = {strength:.0%}")
    ax.set_ylim(-0.05, max(1.35, float(traj.max()) + 0.05))
    ax.legend(loc="lower right")
    toy_label(ax, "TOY MODEL - 1-D push-cart", loc="upper left")
    return fig, outcome


def run(friction=None, mass=None, strength=None, controllers=None):
    """Whole demo. Slider values default to the nominal floor."""
    t0 = time.perf_counter()
    friction = config.DR_NOMINAL["friction"] if friction is None else friction
    mass = config.DR_NOMINAL["mass"] if mass is None else mass
    strength = config.DR_NOMINAL["strength"] if strength is None else strength
    if controllers is None:
        controllers = tune_both()
    results = evaluate(controllers)
    fig_bar = success_bar_figure(results)
    fig_live, outcome = live_figure(controllers, friction, mass, strength)
    return {
        "figures": {"dr_success_rates": fig_bar, "dr_live_trial": fig_live},
        "controllers": {k: v.tolist() for k, v in controllers.items()},
        "results": results,
        "live_outcome": outcome,
        "seconds": time.perf_counter() - t0,
    }


if __name__ == "__main__":
    out = run()
    for name, g in out["controllers"].items():
        print(name, "kp=%.1f kd=%.2f ff=%.2f" % tuple(g))
    for name, r in out["results"].items():
        print(name, {k: round(v, 2) for k, v in r.items()})
    print(f"{out['seconds']:.1f}s")
