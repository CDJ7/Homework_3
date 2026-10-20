"""
actuator_net.py - Slide 2 demo (Hwangbo et al., 2019): the actuator network idea.

*** TOY MODEL - all data here is synthetic. ***
Nothing in this file reproduces numbers from the paper. It only shows WHY a
learned actuator model can beat an ideal or a simple analytical model when the
real actuator has hidden dynamics (a series-elastic spring lag, a communication
delay, friction and a torque limit).

Pipeline:
  1. Simulate a toy "real" actuator and log a few minutes of
     (position error, joint velocity, torque) at 500 Hz.
  2. Train a small MLP that maps a short HISTORY of position error and velocity
     to torque (the paper's actuator-network idea, in miniature).
  3. Compare three torque models on held-out data:
       (a) ideal:      tau = kp*err - kd*vel  (instant, perfect)
       (b) analytical: ideal + torque limit + a guessed first-order lag
       (c) learned:    the MLP
"""
import time

import numpy as np
from scipy.signal import lfilter
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

import config
from demos.style import plt, toy_label


# ----------------------------------------------------------------------------
# 1. Synthetic logs
# ----------------------------------------------------------------------------
def _multisine(t, rng, n, f_lo, f_hi, amp):
    """Sum of n random sines - a smooth, rich excitation signal."""
    out = np.zeros_like(t)
    for _ in range(n):
        f = rng.uniform(f_lo, f_hi)
        out += rng.uniform(0.3, 1.0) * np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi))
    return amp * out / n


def make_motion(seed=config.RANDOM_SEED):
    """Joint motion q(t), velocity dq(t) and position error err(t) = q* - q."""
    rng = np.random.default_rng(seed)
    dt = config.ACT_DT
    t = np.arange(0.0, config.ACT_LOG_SECONDS, dt)
    q = _multisine(t, rng, 6, 0.2, 2.5, 1.2)
    dq = np.gradient(q, dt)
    # Slowly varying envelope so some stretches push the torque limit
    envelope = 0.6 + 0.6 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.02 * t))
    err = envelope * _multisine(t, rng, 8, 0.5, 6.0, 0.7)
    return t, q, dq, err


def _first_order_lag(x, tau, dt):
    """Discrete first-order low-pass y[k+1] = y[k] + a*(x[k] - y[k])."""
    a = dt / (tau + dt)
    return lfilter([a], [1.0, -(1.0 - a)], x)


def _delay(x, steps):
    """Shift a signal by `steps` samples (the communication delay)."""
    if steps <= 0:
        return x.copy()
    return np.concatenate([np.full(steps, x[0]), x[:-steps]])


def toy_real_torque(err, dq, delay_ms, seed=config.RANDOM_SEED):
    """The toy 'real' actuator: delayed PD command -> torque limit ->
    series-elastic spring lag -> friction loss -> sensor noise."""
    rng = np.random.default_rng(seed + 1)
    dt = config.ACT_DT
    d = int(round(delay_ms / 1000.0 / dt))
    cmd = config.ACT_KP * _delay(err, d) - config.ACT_KD * _delay(dq, d)
    cmd = np.clip(cmd, -config.ACT_TORQUE_LIMIT, config.ACT_TORQUE_LIMIT)
    tau = _first_order_lag(cmd, config.ACT_SPRING_TAU, dt)
    tau -= config.ACT_FRICTION * np.tanh(dq / 0.05)
    tau += rng.normal(0.0, 0.15, size=tau.shape)
    return tau


# ----------------------------------------------------------------------------
# 2. The three torque models
# ----------------------------------------------------------------------------
def ideal_model(err, dq):
    """(a) Ideal actuator: produces exactly the PD torque, instantly."""
    return config.ACT_KP * err - config.ACT_KD * dq


def analytical_model(err, dq):
    """(b) Simple analytical model: PD + torque limit + a GUESSED spring lag.
    It does not know about the delay or the friction."""
    cmd = np.clip(ideal_model(err, dq), -config.ACT_TORQUE_LIMIT, config.ACT_TORQUE_LIMIT)
    return _first_order_lag(cmd, config.ACT_ANALYTIC_TAU_GUESS, config.ACT_DT)


def history_features(err, dq):
    """Stack a short history of position error and velocity, e.g. taps at
    0, 10, 20 and 30 ms ago -> 8 input features per sample."""
    cols = []
    for k in config.ACT_HISTORY_STEPS:
        cols.append(_delay(err, k))
        cols.append(_delay(dq, k))
    return np.stack(cols, axis=1)


def train_actuator_net(X, y, seed=config.RANDOM_SEED):
    """(c) Train the small MLP on a random subsample of the training logs."""
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(X), size=min(config.ACT_TRAIN_SAMPLES, len(X)), replace=False)
    scaler = StandardScaler().fit(X[idx])
    net = MLPRegressor(hidden_layer_sizes=config.ACT_HIDDEN, activation="tanh",
                       learning_rate_init=3e-3, max_iter=config.ACT_MAX_ITER,
                       early_stopping=True, n_iter_no_change=15, random_state=seed)
    net.fit(scaler.transform(X[idx]), y[idx])
    return scaler, net


def rmse(a, b):
    return float(np.sqrt(np.mean((a - b) ** 2)))


# ----------------------------------------------------------------------------
# 3. Demo entry points
# ----------------------------------------------------------------------------
def delay_sweep(delays_ms=None):
    """Ideal-model and analytical-model error versus communication delay.
    Cheap: no training, so the slider can update instantly."""
    if delays_ms is None:
        delays_ms = np.arange(0, config.ACT_MAX_DELAY_MS + 1, 2)
    _, _, dq, err = make_motion()
    n_test = int(config.ACT_TEST_SECONDS / config.ACT_DT)
    ideal = ideal_model(err, dq)[-n_test:]
    analytic = analytical_model(err, dq)[-n_test:]
    ideal_err, analytic_err = [], []
    for d in delays_ms:
        real = toy_real_torque(err, dq, d)[-n_test:]
        ideal_err.append(rmse(ideal, real))
        analytic_err.append(rmse(analytic, real))
    return np.asarray(delays_ms), np.asarray(ideal_err), np.asarray(analytic_err)


def run(delay_ms=config.ACT_DEFAULT_DELAY_MS):
    """Run the whole actuator demo. Returns figures and measured metrics."""
    t0 = time.perf_counter()
    t, q, dq, err = make_motion()
    real = toy_real_torque(err, dq, delay_ms)

    n_test = int(config.ACT_TEST_SECONDS / config.ACT_DT)
    X = history_features(err, dq)
    X_train, y_train = X[:-n_test], real[:-n_test]
    X_test = X[-n_test:]

    scaler, net = train_actuator_net(X_train, y_train)
    preds = {
        "(a) Ideal model": ideal_model(err, dq)[-n_test:],
        "(b) Analytical model": analytical_model(err, dq)[-n_test:],
        "(c) Learned actuator net": net.predict(scaler.transform(X_test)),
    }
    real_test = real[-n_test:]
    errors = {name: rmse(p, real_test) for name, p in preds.items()}
    t_test = t[-n_test:] - t[-n_test]

    # ---- Figure 1: predicted vs "real" torque + error bars -----------------
    fig = plt.figure(figsize=(11.5, 6.2))
    gs = fig.add_gridspec(3, 2, width_ratios=[3.2, 1.2], hspace=0.45, wspace=0.25)
    window = (t_test >= 5.0) & (t_test <= 6.5)  # 1.5 s zoom window
    colors = [config.GREY, config.ACCENT_2, config.ACCENT]
    for i, (name, p) in enumerate(preds.items()):
        ax = fig.add_subplot(gs[i, 0])
        ax.plot(t_test[window], real_test[window], color=config.NAVY, lw=2.2, label='"Real" torque (toy)')
        ax.plot(t_test[window], p[window], color=colors[i], lw=2, ls="--", label=name)
        ax.set_ylabel("N·m")
        ax.set_title(f"{name}   RMSE = {errors[name]:.2f} N·m", loc="left", fontsize=12.5)
        ax.set_ylim(real_test[window].min() * 1.35, real_test[window].max() * 1.35)
        if i == 2:
            ax.set_xlabel("time in held-out test log (s)")
    fig.suptitle(f'Solid navy = "real" torque from the toy actuator (delay = {delay_ms} ms)   ·   '
                 "dashed = model prediction   ·   TOY MODEL, synthetic logs",
                 x=0.06, ha="left", fontsize=12, color=config.ACCENT_3, fontweight="bold")
    axb = fig.add_subplot(gs[:, 1])
    bars = axb.bar(["Ideal", "Analytical", "Learned"], list(errors.values()), color=colors)
    for b, v in zip(bars, errors.values()):
        axb.text(b.get_x() + b.get_width() / 2, v, f"{v:.2f}", ha="center", va="bottom",
                 fontsize=12, fontweight="bold")
    axb.set_title("Test RMSE (N·m)")
    axb.set_ylim(0, max(errors.values()) * 1.2)
    axb.grid(axis="x", visible=False)

    # ---- Figure 2: ideal-model error vs delay ---------------------------------
    delays, ideal_err, analytic_err = delay_sweep()
    fig2, ax2 = plt.subplots(figsize=(8, 4.2))
    ax2.plot(delays, ideal_err, "o-", color=config.GREY, lw=2.2, label="(a) Ideal model")
    ax2.plot(delays, analytic_err, "s-", color=config.ACCENT_2, lw=2.2, label="(b) Analytical model")
    ax2.axvline(delay_ms, color=config.ACCENT, lw=2, ls=":")
    ax2.scatter([delay_ms], [errors["(c) Learned actuator net"]], s=140, color=config.ACCENT,
                zorder=5, label=f"(c) Learned net at {delay_ms} ms")
    ax2.set_xlabel("communication delay in the toy actuator (ms)")
    ax2.set_ylabel("test RMSE (N·m)")
    ax2.set_title("Hand-written models get worse as the hidden delay grows")
    ax2.set_ylim(bottom=0)
    ax2.legend(loc="upper left")
    toy_label(ax2, "TOY MODEL - synthetic data", loc="lower right")

    return {
        "figures": {"actuator_comparison": fig, "actuator_delay_sweep": fig2},
        "errors": errors,
        "sweep": {"delay_ms": delays.tolist(), "ideal_rmse": ideal_err.tolist(),
                  "analytical_rmse": analytic_err.tolist()},
        "delay_ms": delay_ms,
        "n_samples": len(t),
        "log_minutes": config.ACT_LOG_SECONDS / 60,
        "seconds": time.perf_counter() - t0,
    }


if __name__ == "__main__":
    out = run()
    print({k: round(v, 3) for k, v in out["errors"].items()}, f"{out['seconds']:.1f}s")
