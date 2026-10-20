"""
mock_unitree.py - a tiny, OFFLINE stand-in for unitree_sdk2_python.

*** MOCK ONLY. This file never opens a network socket and never talks to a
robot. It copies the SHAPE of the real SDK's API so the presentation can show
how a policy would plug into the Go2, without installing CycloneDDS. ***

What each mock mirrors in the real SDK (unitree_sdk2_python on GitHub):

  Mock class / function           Real SDK counterpart
  ------------------------------  ------------------------------------------------
  ChannelFactoryInitialize        unitree_sdk2py.core.channel.ChannelFactoryInitialize
                                  (starts DDS on the Ethernet interface to the robot)
  MockChannelPublisher            unitree_sdk2py.core.channel.ChannelPublisher
  MockChannelSubscriber           unitree_sdk2py.core.channel.ChannelSubscriber
  TOPIC_LOWSTATE = "rt/lowstate"  low-level state topic used by the Go2 examples
  TOPIC_LOWCMD   = "rt/lowcmd"    low-level command topic used by the Go2 examples
  MockLowState                    LowState_ message (unitree_go IDL): imu_state,
                                  motor_state[...], foot_force, battery info
  MockLowCmd                      LowCmd_ message: motor_cmd[...] with q, dq, kp, kd, tau
  MockSportClient                 unitree_sdk2py.go2.sport.sport_client.SportClient
                                  (StandUp, BalanceStand, RecoveryStand, Move(vx, vy, vyaw))
  MockMotionSwitcherClient        MotionSwitcherClient - used in the Go2 stand example
                                  to switch off the built-in sport mode before
                                  low-level control

Communication in the real SDK is DDS publish/subscribe on named topics; here a
Python dict plays the role of the DDS bus. The real Go2 stand example sends a
LowCmd every 2 ms.

Notes on simplifications:
  * The real LowState/LowCmd messages reserve more motor slots than the Go2's
    12 motors and carry extra fields (mode flags, CRC, etc.). The mock keeps
    only the 12 motors and the fields used in this presentation.
  * The physics behind the mock is a toy (each joint is a damped inertia
    driven by the PD law); it is NOT a model of the Go2.
"""
import importlib.util
import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List

import numpy as np

TOPIC_LOWSTATE = "rt/lowstate"
TOPIC_LOWCMD = "rt/lowcmd"
NUM_MOTORS = 12  # Go2: 4 legs x (hip, thigh, calf)


def real_sdk_available() -> bool:
    """True if unitree_sdk2py is importable. The app only shows a badge;
    it NEVER uses the real SDK to send commands."""
    return importlib.util.find_spec("unitree_sdk2py") is not None


# ----------------------------------------------------------------------------
# Message types (mirror LowState_ / LowCmd_ field names)
# ----------------------------------------------------------------------------
@dataclass
class MockIMUState:                 # mirrors LowState_.imu_state
    quaternion: List[float] = field(default_factory=lambda: [1.0, 0.0, 0.0, 0.0])  # w, x, y, z
    gyroscope: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])       # rad/s
    accelerometer: List[float] = field(default_factory=lambda: [0.0, 0.0, 9.81])  # m/s^2
    rpy: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])             # roll, pitch, yaw


@dataclass
class MockMotorState:               # mirrors LowState_.motor_state[i]
    q: float = 0.0                  # joint position (rad)
    dq: float = 0.0                 # joint velocity (rad/s)
    tau_est: float = 0.0            # estimated torque (N*m)
    temperature: int = 30           # deg C


@dataclass
class MockLowState:                 # mirrors LowState_
    imu_state: MockIMUState = field(default_factory=MockIMUState)
    motor_state: List[MockMotorState] = field(
        default_factory=lambda: [MockMotorState() for _ in range(NUM_MOTORS)])
    foot_force: List[int] = field(default_factory=lambda: [0, 0, 0, 0])
    power_v: float = 28.0           # battery voltage (mock)
    tick: int = 0


@dataclass
class MockMotorCmd:                 # mirrors LowCmd_.motor_cmd[i]
    q: float = 0.0                  # target position (rad)
    dq: float = 0.0                 # target velocity (rad/s)
    kp: float = 0.0                 # position gain
    kd: float = 0.0                 # damping gain
    tau: float = 0.0                # feed-forward torque (N*m)


@dataclass
class MockLowCmd:                   # mirrors LowCmd_
    motor_cmd: List[MockMotorCmd] = field(
        default_factory=lambda: [MockMotorCmd() for _ in range(NUM_MOTORS)])


# ----------------------------------------------------------------------------
# A fake DDS bus + publisher / subscriber
# ----------------------------------------------------------------------------
_BUS: Dict[str, list] = {}          # topic -> list of subscriber callbacks
_INITIALISED = {"done": False}


def ChannelFactoryInitialize(domain_id: int = 0, network_interface: str = "mock0"):
    """Mirror of ChannelFactoryInitialize(id, "eth0"). Mock: no network."""
    _BUS.clear()
    _INITIALISED["done"] = True


class MockChannelPublisher:
    def __init__(self, topic: str, msg_type=None):
        self.topic = topic

    def Init(self):
        _BUS.setdefault(self.topic, [])

    def Write(self, msg):
        for cb in _BUS.get(self.topic, []):
            cb(msg)


class MockChannelSubscriber:
    def __init__(self, topic: str, msg_type=None):
        self.topic = topic

    def Init(self, handler: Callable, queue_len: int = 10):
        _BUS.setdefault(self.topic, []).append(handler)


# ----------------------------------------------------------------------------
# Toy robot behind the bus
# ----------------------------------------------------------------------------
class MockGo2:
    """Subscribes to rt/lowcmd, steps a toy joint model, publishes rt/lowstate."""

    def __init__(self, default_pose, dt=0.002, seed=0):
        self.dt = dt
        self.rng = np.random.default_rng(seed)
        self.q = np.array(default_pose, dtype=float) + self.rng.normal(0, 0.05, NUM_MOTORS)
        self.dq = np.zeros(NUM_MOTORS)
        self.tau = np.zeros(NUM_MOTORS)
        self.sport_mode_on = True
        self.state = MockLowState()
        self._pub = MockChannelPublisher(TOPIC_LOWSTATE)
        self._pub.Init()
        MockChannelSubscriber(TOPIC_LOWCMD).Init(self._on_lowcmd)
        self._publish_state()

    def _on_lowcmd(self, cmd: MockLowCmd):
        if self.sport_mode_on:
            # On the real robot the built-in controller would fight us.
            raise RuntimeError("Sport mode is still on - release it with MotionSwitcherClient first.")
        q_des = np.array([m.q for m in cmd.motor_cmd])
        dq_des = np.array([m.dq for m in cmd.motor_cmd])
        kp = np.array([m.kp for m in cmd.motor_cmd])
        kd = np.array([m.kd for m in cmd.motor_cmd])
        ff = np.array([m.tau for m in cmd.motor_cmd])
        self.tau = kp * (q_des - self.q) + kd * (dq_des - self.dq) + ff
        inertia, damping = 0.05, 0.2                       # toy values
        self.dq += self.dt * (self.tau - damping * self.dq) / inertia
        self.q += self.dt * self.dq
        self._publish_state()

    def _publish_state(self):
        s = self.state
        s.tick += 1
        for i, m in enumerate(s.motor_state):
            m.q, m.dq, m.tau_est = float(self.q[i]), float(self.dq[i]), float(self.tau[i])
        g = self.rng.normal(0, 0.02, 3)                      # noisy gyro
        s.imu_state.gyroscope = g.tolist()
        roll, pitch = 0.02 * math.sin(0.01 * s.tick), 0.01 * math.cos(0.013 * s.tick)
        s.imu_state.rpy = [roll, pitch, 0.0]
        s.imu_state.quaternion = [math.cos(roll / 2) * math.cos(pitch / 2), math.sin(roll / 2),
                                  math.sin(pitch / 2), 0.0]
        s.foot_force = [int(40 + 5 * self.rng.normal()) for _ in range(4)]
        self._pub.Write(s)


class MockMotionSwitcherClient:
    """Mirror of MotionSwitcherClient: CheckMode() / ReleaseMode()."""

    def __init__(self, robot: MockGo2):
        self.robot = robot

    def Init(self):
        pass

    def CheckMode(self):
        return (0, {"name": "sport" if self.robot.sport_mode_on else ""})

    def ReleaseMode(self):
        self.robot.sport_mode_on = False
        return 0


# ----------------------------------------------------------------------------
# High-level SportClient mock
# ----------------------------------------------------------------------------
class MockSportClient:
    """Mirror of SportClient on the Go2. Move(vx, vy, vyaw) sends body-frame
    forward, sideways and turning velocities to Unitree's own walking
    controller. Here the 'walking controller' is a kinematic integrator."""

    def __init__(self, x=0.0, y=0.0, yaw=0.0):
        self.x, self.y, self.yaw = x, y, yaw
        self.cmd = (0.0, 0.0, 0.0)
        self.standing = False
        self.log: List[tuple] = []

    def SetTimeout(self, seconds: float):
        pass

    def Init(self):
        pass

    def StandUp(self):
        self.standing = True
        return 0

    def BalanceStand(self):
        self.standing = True
        return 0

    def RecoveryStand(self):
        self.standing = True
        return 0

    def StopMove(self):
        self.cmd = (0.0, 0.0, 0.0)
        return 0

    def Move(self, vx: float, vy: float, vyaw: float):
        if not self.standing:
            raise RuntimeError("Call StandUp()/BalanceStand() before Move().")
        self.cmd = (float(vx), float(vy), float(vyaw))
        self.log.append(self.cmd)
        return 0

    def step(self, dt: float):
        """Mock-only: advance the dog's pose by dt using the last command."""
        vx, vy, vyaw = self.cmd
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        self.x += dt * (c * vx - s * vy)
        self.y += dt * (s * vx + c * vy)
        self.yaw += dt * vyaw
