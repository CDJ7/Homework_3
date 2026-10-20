"""
sdk_demo.py - Slide 5 demo: where the policy meets the (mock) Go2.

(a) Low-level policy loop, on the MOCK SDK:
      LowState -> observation vector -> tiny network -> q targets in LowCmd
    The command loop ticks every 2 ms; the policy runs every
    config.SDK_POLICY_DECIMATION ticks and the motors track the latest target
    in between. The network has RANDOM, UNTRAINED weights: it only shows the
    data flow, not a walking gait.

(b) High-level investigation layer:
    A synthetic stain cluster on a top-down mini-map creates an "interest"
    map. The investigation layer picks the most interesting spot and sends
    SportClient.Move(vx, vy, vyaw) commands to walk there, then the next one.
"""
import io
import math
import time

import numpy as np
from PIL import Image

import config
import mock_unitree as mu
from demos.style import plt, toy_label

OBS_NAMES = (["ang_vel_x", "ang_vel_y", "ang_vel_z"]
             + ["gravity_x", "gravity_y", "gravity_z"]
             + ["cmd_vx", "cmd_vy", "cmd_vyaw"]
             + [f"q_err_{i}" for i in range(12)]
             + [f"dq_{i}" for i in range(12)]
             + [f"last_action_{i}" for i in range(12)])
OBS_DIM = len(OBS_NAMES)  # 45


# ----------------------------------------------------------------------------
# (a) Policy loop
# ----------------------------------------------------------------------------
class TinyPolicy:
    """45 -> 32 -> 12 MLP with tanh output (bounded actions, as in the
    primary reading's advice). Random weights - for data-flow demo only."""

    def __init__(self, seed=config.RANDOM_SEED):
        rng = np.random.default_rng(seed)
        self.W1 = rng.normal(0, 1 / math.sqrt(OBS_DIM), (OBS_DIM, 32))
        self.b1 = np.zeros(32)
        self.W2 = rng.normal(0, 1 / math.sqrt(32), (32, 12))
        self.b2 = np.zeros(12)

    def __call__(self, obs):
        return np.tanh(np.tanh(obs @ self.W1 + self.b1) @ self.W2 + self.b2)


def projected_gravity(quat):
    """Gravity direction in the body frame from a (w, x, y, z) quaternion."""
    w, x, y, z = quat
    return np.array([2 * (w * y - x * z),
                     -2 * (y * z + w * x),
                     -(1 - 2 * (x * x + y * y))])


def build_observation(state: mu.MockLowState, command, last_action):
    """LowState -> observation vector (example 45-D layout)."""
    imu = state.imu_state
    q = np.array([m.q for m in state.motor_state])
    dq = np.array([m.dq for m in state.motor_state])
    return np.concatenate([np.array(imu.gyroscope), projected_gravity(imu.quaternion),
                           np.array(command), q - np.array(config.SDK_DEFAULT_POSE), dq,
                           last_action])


def run_policy_loop(ticks=config.SDK_LOOP_TICKS, command=(0.3, 0.0, 0.0)):
    """Run the mock 2 ms loop and record everything the slide displays."""
    mu.ChannelFactoryInitialize(0, "mock0")
    robot = mu.MockGo2(config.SDK_DEFAULT_POSE, dt=config.SDK_CONTROL_DT, seed=config.RANDOM_SEED)
    switcher = mu.MockMotionSwitcherClient(robot)
    switcher.Init()
    switcher.ReleaseMode()                 # switch off sport mode first (safety step)

    latest = {}
    mu.MockChannelSubscriber(mu.TOPIC_LOWSTATE).Init(lambda msg: latest.__setitem__("state", msg))
    pub = mu.MockChannelPublisher(mu.TOPIC_LOWCMD)
    pub.Init()
    robot._publish_state()                 # first LowState arrives

    policy = TinyPolicy()
    action = np.zeros(12)
    q_target = np.array(config.SDK_DEFAULT_POSE, dtype=float)
    hist_t, hist_q, hist_target = [], [], []
    snapshots = []
    for k in range(ticks):
        state = latest["state"]
        if k % config.SDK_POLICY_DECIMATION == 0:
            obs = build_observation(state, command, action)
            action = policy(obs)
            q_target = np.array(config.SDK_DEFAULT_POSE) + config.SDK_ACTION_SCALE * action
        cmd = mu.MockLowCmd()
        for i, m in enumerate(cmd.motor_cmd):
            m.q, m.dq, m.kp, m.kd, m.tau = float(q_target[i]), 0.0, config.SDK_KP, config.SDK_KD, 0.0
        if k % config.SDK_POLICY_DECIMATION == 0:
            snapshots.append({"tick": k, "obs": obs.copy(),
                              "cmd": [(m.q, m.dq, m.kp, m.kd, m.tau) for m in cmd.motor_cmd]})
        pub.Write(cmd)                     # robot steps and publishes new LowState
        hist_t.append(k * config.SDK_CONTROL_DT)
        hist_q.append([m.q for m in latest["state"].motor_state])
        hist_target.append(q_target.copy())
    return {"t": np.array(hist_t), "q": np.array(hist_q), "target": np.array(hist_target),
            "snapshots": snapshots}


def policy_loop_figure(loop):
    fig, ax = plt.subplots(figsize=(8.5, 4.0))
    names = ["hip", "thigh", "calf"]
    cols = [config.NAVY, config.ACCENT, config.ACCENT_2]
    for j in range(3):
        ax.step(loop["t"], loop["target"][:, j], where="post", color=cols[j], lw=1.8, ls="--",
                label=f"{names[j]} target (LowCmd.q)")
        ax.plot(loop["t"], loop["q"][:, j], color=cols[j], lw=2.4, label=f"{names[j]} measured (LowState.q)")
    ax.set_xlabel("time (s) - 2 ms command ticks")
    ax.set_ylabel("rad")
    ax.set_title(f"Leg 1: policy updates every {config.SDK_POLICY_DECIMATION * config.SDK_CONTROL_DT * 1000:.0f} ms, "
                 f"motors track the latest target")
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=9.5)
    toy_label(ax, "MOCK SDK - random untrained network", loc="lower right")
    return fig


# ----------------------------------------------------------------------------
# (b) Investigation layer
# ----------------------------------------------------------------------------
def make_stains(seed=config.RANDOM_SEED):
    """Synthetic bloodstain drops: one dense cluster, one smaller, some spatter."""
    rng = np.random.default_rng(seed)
    S = config.SDK_MAP_SIZE
    big = rng.normal([5.6, 5.2], [0.35, 0.3], (int(config.SDK_N_STAINS * 0.55), 2))
    small = rng.normal([2.4, 5.8], [0.25, 0.25], (int(config.SDK_N_STAINS * 0.25), 2))
    trail = np.stack([np.linspace(2.6, 5.4, 20), np.linspace(5.6, 5.3, 20)], 1) + rng.normal(0, 0.12, (20, 2))
    spatter = rng.uniform(0.5, S - 0.5, (config.SDK_N_STAINS - len(big) - len(small) - 20, 2))
    return np.clip(np.vstack([big, small, trail, spatter]), 0, S)


def interest_map(stains, grid=80, bw=0.35):
    """Kernel-density 'interest' over the floor: more stains -> more interest."""
    xs = np.linspace(0, config.SDK_MAP_SIZE, grid)
    X, Y = np.meshgrid(xs, xs)
    pts = np.stack([X.ravel(), Y.ravel()], 1)
    d2 = ((pts[:, None, :] - stains[None, :, :]) ** 2).sum(-1)
    Z = np.exp(-d2 / (2 * bw ** 2)).sum(1).reshape(grid, grid)
    return xs, Z / Z.max()


def run_investigation(stains=None):
    stains = make_stains() if stains is None else stains
    xs, Z = interest_map(stains)
    remaining = Z.copy()
    sport = mu.MockSportClient(x=0.8, y=0.8, yaw=0.0)
    sport.Init()
    sport.StandUp()
    sport.BalanceStand()
    path, cmds, visited = [(sport.x, sport.y, sport.yaw)], [], []
    target, pause = None, 0
    X, Y = np.meshgrid(xs, xs)
    for _ in range(config.SDK_SEARCH_STEPS):
        if target is None:
            if remaining.max() < 0.35 or len(visited) >= 3:
                break
            iy, ix = np.unravel_index(np.argmax(remaining), remaining.shape)
            target = np.array([xs[ix], xs[iy]])
        if pause > 0:                         # "sniffing" at a spot
            sport.StopMove()
            pause -= 1
        else:
            dx, dy = target[0] - sport.x, target[1] - sport.y
            dist = math.hypot(dx, dy)
            if dist < 0.25:
                visited.append(target.copy())
                remaining = remaining * (1 - np.exp(-((X - target[0]) ** 2 + (Y - target[1]) ** 2) / (2 * 0.8 ** 2)))
                target, pause = None, 10
                sport.StopMove()
            else:
                heading_err = math.atan2(dy, dx) - sport.yaw
                heading_err = (heading_err + math.pi) % (2 * math.pi) - math.pi
                vyaw = float(np.clip(2.0 * heading_err, -config.SDK_MAX_VYAW, config.SDK_MAX_VYAW))
                vx = float(np.clip(0.8 * dist, 0, config.SDK_MAX_VX) * max(0.0, math.cos(heading_err)))
                # body-frame sideways correction
                vy = float(np.clip(0.5 * (-math.sin(sport.yaw) * dx + math.cos(sport.yaw) * dy)
                                   * (1 if abs(heading_err) < 0.5 else 0), -0.2, 0.2))
                sport.Move(vx, vy, vyaw)
        cmds.append(sport.cmd)
        sport.step(config.SDK_MOVE_DT)
        path.append((sport.x, sport.y, sport.yaw))
    return {"stains": stains, "xs": xs, "Z": Z, "path": np.array(path), "cmds": np.array(cmds),
            "visited": np.array(visited)}


def _draw_map(ax, inv, upto=None):
    S = config.SDK_MAP_SIZE
    ax.imshow(inv["Z"], origin="lower", extent=[0, S, 0, S], cmap="Reds", alpha=0.55, vmin=0, vmax=1)
    ax.scatter(inv["stains"][:, 0], inv["stains"][:, 1], s=9, color="#8B0000", alpha=0.8, label="stain drops (synthetic)")
    p = inv["path"] if upto is None else inv["path"][:upto]
    ax.plot(p[:, 0], p[:, 1], color=config.NAVY, lw=2.5, label="dog path (Move commands)")
    x, y, yaw = p[-1]
    ax.scatter([x], [y], s=160, color=config.ACCENT, edgecolor=config.NAVY, zorder=5, label="Go2 (mock)")
    ax.arrow(x, y, 0.45 * math.cos(yaw), 0.45 * math.sin(yaw), width=0.04, color=config.NAVY, zorder=6)
    n_vis = len(inv["visited"]) if upto is None else sum(
        1 for v in inv["visited"] if np.min(np.hypot(p[:, 0] - v[0], p[:, 1] - v[1])) < 0.3)
    for i, v in enumerate(inv["visited"][:n_vis]):
        ax.scatter([v[0]], [v[1]], marker="X", s=150, color=config.ACCENT_2, edgecolor="white", zorder=6)
        ax.text(v[0] + 0.15, v[1] + 0.2, f"spot {i + 1}", fontsize=10, fontweight="bold", color=config.NAVY)
    ax.set_xlim(0, S)
    ax.set_ylim(0, S)
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")


def investigation_figure(inv):
    fig, ax = plt.subplots(figsize=(6.8, 6.0))
    _draw_map(ax, inv)
    ax.set_title("Investigation layer: interest map -> Move(vx, vy, vyaw)")
    ax.legend(loc="lower right", fontsize=9)
    toy_label(ax, "SYNTHETIC SCENE - mock SDK", loc="upper left")
    return fig


def investigation_gif(inv, n_frames=40):
    fig, ax = plt.subplots(figsize=(5.0, 5.0), dpi=80)
    frames = []
    idx = np.linspace(2, len(inv["path"]), n_frames).astype(int)
    for k in idx:
        ax.clear()
        _draw_map(ax, inv, upto=k)
        vx, vy, vyaw = inv["cmds"][min(k, len(inv["cmds"])) - 1]
        ax.set_title(f"t = {k * config.SDK_MOVE_DT:4.1f} s   Move({vx:.2f}, {vy:.2f}, {vyaw:.2f})", fontsize=11)
        fig.canvas.draw()
        frames.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba())).convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT))
    plt.close(fig)
    buf = io.BytesIO()
    frames[0].save(buf, format="GIF", save_all=True, append_images=frames[1:] + [frames[-1]] * 8,
                   duration=120, loop=0)
    return buf.getvalue()


def run(with_gif=True):
    t0 = time.perf_counter()
    loop = run_policy_loop()
    inv = run_investigation()
    out = {
        "figures": {"sdk_policy_loop": policy_loop_figure(loop), "sdk_investigation": investigation_figure(inv)},
        "loop": loop,
        "investigation": inv,
        "gif": investigation_gif(inv) if with_gif else None,
        "real_sdk": mu.real_sdk_available(),
        "n_move_cmds": int(np.sum(np.abs(inv["cmds"]).sum(1) > 0)),
        "n_spots": len(inv["visited"]),
    }
    out["seconds"] = time.perf_counter() - t0
    return out


if __name__ == "__main__":
    o = run()
    print("spots", o["n_spots"], "moves", o["n_move_cmds"], "steps", len(o["investigation"]["cmds"]),
          f"{o['seconds']:.1f}s", "real sdk:", o["real_sdk"])
