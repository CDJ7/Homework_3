"""
config.py - every setting for the Readings 5 presentation lives here.

Change values in this file instead of hunting through the demo modules.
All paths use pathlib so the project works the same on Windows and Linux.
"""
from pathlib import Path

# ----------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
FIGURE_DIR = OUTPUT_DIR / "figures"
PPTX_PATH = OUTPUT_DIR / "Readings5_Presentation.pptx"

# Bundled synthetic Kine2Go-style sample (used when the download fails)
KINE2GO_SYNTHETIC_PATH = DATA_DIR / "kine2go_synthetic_sample" / "motion_SYNTHETIC.npy"
# Where a real downloaded motion.npy is cached
KINE2GO_CACHE_DIR = DATA_DIR / "kine2go_cache"

# ----------------------------------------------------------------------------
# Presentation info
# ----------------------------------------------------------------------------
PRESENTATION_TITLE = "Readings 5: From Research to a Crime-Scene Robot Dog"
AUTHOR = "Connor Jarrett"
COURSE = "ENGR 6010 - AI in Robotics"
PRESENTATION_DATE = "October 20, 2026"

# ----------------------------------------------------------------------------
# Theme (shared by the Streamlit app, matplotlib figures and the PPTX export)
# ----------------------------------------------------------------------------
NAVY = "#0B1F3A"        # title bar
NAVY_LIGHT = "#1C3559"
ACCENT = "#F5A623"      # orange accent
ACCENT_2 = "#2EC4B6"    # teal accent
ACCENT_3 = "#E5484D"    # red (bloodstains / errors)
GREY = "#6B7785"
TEXT_DARK = "#14202E"
BG_LIGHT = "#F6F8FB"

# One color per source, used in the pipeline diagram and summary table
SOURCE_COLORS = {
    "Hwangbo et al. (2019)": "#F5A623",
    "Gurram et al. (2024)": "#2EC4B6",
    "Kine2Go dataset": "#8E6CEF",
    "unitree_sdk2_python": "#E5484D",
}

FIG_DPI = 150           # PNG resolution for exported figures
RANDOM_SEED = 7         # every demo is seeded so results are repeatable

# ----------------------------------------------------------------------------
# Demo 1 - Actuator network (Hwangbo et al.)  *** TOY MODEL ***
# ----------------------------------------------------------------------------
ACT_DT = 0.002                  # 500 Hz log rate (s)
ACT_LOG_SECONDS = 180           # "a few minutes" of synthetic logs
ACT_TEST_SECONDS = 30           # last 30 s held out for testing
ACT_DEFAULT_DELAY_MS = 10       # slider default
ACT_MAX_DELAY_MS = 20           # slider max
ACT_KP = 40.0                   # PD gains inside the toy actuator (N*m/rad)
ACT_KD = 0.6                    # (N*m*s/rad)
ACT_SPRING_TAU = 0.012          # series-elastic spring lag time constant (s)
ACT_TORQUE_LIMIT = 30.0         # toy torque limit (N*m)
ACT_FRICTION = 0.8              # toy Coulomb friction loss (N*m)
ACT_ANALYTIC_TAU_GUESS = 0.006  # analytical model's (wrong) guess of the lag
ACT_HISTORY_STEPS = (0, 5, 10, 15)  # history taps: 0, 10, 20, 30 ms ago
ACT_TRAIN_SAMPLES = 20000       # subsample for fast training
ACT_HIDDEN = (32, 32)           # MLP hidden layers (toy choice)
ACT_MAX_ITER = 300

# ----------------------------------------------------------------------------
# Demo 2 - Domain randomization (survey)  *** TOY 1-D PUSH-CART ***
# ----------------------------------------------------------------------------
DR_DT = 0.02                    # 50 Hz simulation
DR_HORIZON_S = 6.0              # time limit per episode (s)
DR_GOAL = 1.0                   # move the cart 1 m
DR_POS_TOL = 0.05               # success: within 5 cm ...
DR_VEL_TOL = 0.05               # ... and nearly stopped (m/s)
DR_HOLD_S = 0.5                 # ... for at least 0.5 s at the end
DR_FORCE_LIMIT = 8.0            # max motor force (N) at strength 1.0
DR_NOMINAL = {"friction": 0.10, "mass": 1.0, "strength": 1.0}
DR_RANDOM_RANGES = {            # ranges used for randomized tuning
    "friction": (0.02, 0.45),
    "mass": (0.6, 2.5),
    "strength": (0.6, 1.4),
}
DR_N_CANDIDATES = 1000          # random-search candidates (controller gains)
DR_N_TRAIN_ENVS = 64            # environments per candidate when randomizing
DR_N_TEST_ENVS = 200            # environments per test condition
# Shifted test conditions (each is a small range around a scenario)
DR_TEST_CONDITIONS = {
    "Nominal floor": {"friction": (0.08, 0.12), "mass": (0.9, 1.1), "strength": (0.95, 1.05)},
    "Slippery (wet)": {"friction": (0.02, 0.05), "mass": (0.9, 1.1), "strength": (0.95, 1.05)},
    "Carpet (high friction)": {"friction": (0.30, 0.45), "mass": (0.9, 1.1), "strength": (0.95, 1.05)},
    "Heavier payload": {"friction": (0.08, 0.12), "mass": (1.8, 2.5), "strength": (0.95, 1.05)},
    "Weak motor": {"friction": (0.08, 0.12), "mass": (0.9, 1.1), "strength": (0.6, 0.75)},
    "Random mix": DR_RANDOM_RANGES,
}

# ----------------------------------------------------------------------------
# Demo 3 - Kine2Go
# ----------------------------------------------------------------------------
KINE2GO_REPO_ID = "MIMUW-Robotics/kine2go"
KINE2GO_REPO_TYPE = "dataset"
KINE2GO_TARGET_NAME = "motion.npy"
KINE2GO_TIMEOUT_S = 25          # give up on the network after this long
KINE2GO_FPS = 60                # from the notes: logged at 60 Hz
KINE2GO_N_COLS = 61             # from the notes: motion.npy has shape (T, 61)
KINE2GO_FOOT_COLS = slice(36, 48)  # from the notes: foot positions, 4 feet x (x, y, z)
# The rest of the 61-column layout below is the layout THIS APP ASSUMES so that
# it can plot the data. Only (T, 61) and the foot columns 36:48 come from the
# notes; check the dataset card before relying on the other column meanings.
KINE2GO_ASSUMED_LAYOUT = {
    "joint_pos": slice(0, 12),      # 12 joint angles (rad), 3 per leg
    "joint_vel": slice(12, 24),     # 12 joint velocities (rad/s)
    "actions": slice(24, 36),       # 12 policy actions
    "foot_pos": slice(36, 48),      # 4 feet x (x, y, z) in metres
    "base_pos": slice(48, 51),      # base position (m)
    "base_quat": slice(51, 55),     # base orientation quaternion
    "base_lin_vel": slice(55, 58),  # base linear velocity (m/s)
    "base_ang_vel": slice(58, 61),  # base angular velocity (rad/s)
}
KINE2GO_FOOT_NAMES = ["Foot 1", "Foot 2", "Foot 3", "Foot 4"]
KINE2GO_JOINT_NAMES = ["hip", "thigh", "calf"]

# ----------------------------------------------------------------------------
# Demo 4 - Mock Unitree SDK
# ----------------------------------------------------------------------------
SDK_CONTROL_DT = 0.002          # 2 ms command loop (from the notes, Go2 stand example)
SDK_POLICY_DECIMATION = 10      # policy runs every 10 ticks (50 Hz) - our choice
SDK_LOOP_TICKS = 500            # 1 s of mock control loop
SDK_KP = 20.0                   # mock PD gains written into LowCmd
SDK_KD = 0.5
SDK_ACTION_SCALE = 0.25         # rad, scales the tiny network's tanh output
# Default standing pose (hip, thigh, calf) x 4 legs - mock values
SDK_DEFAULT_POSE = [0.0, 0.8, -1.5] * 4
SDK_MAP_SIZE = 8.0              # crime-scene mini-map is 8 m x 8 m
SDK_N_STAINS = 140              # synthetic stain drops
SDK_MOVE_DT = 0.1               # high-level Move() commands at 10 Hz
SDK_MAX_VX = 0.6                # m/s cap on Move(vx) for careful search
SDK_MAX_VYAW = 1.0              # rad/s cap on Move(vyaw)
SDK_SEARCH_STEPS = 400          # max high-level steps (40 s)
