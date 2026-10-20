"""
content.py - all slide text in one place, shared by app.py and export_pptx.py.

Every factual statement about the four sources comes from my Readings 5 notes.
Anything produced by the demos is labelled as a toy model / synthetic data.
"""
import config

# Short names used across slides
HWANGBO = "Hwangbo et al. (2019)"
SURVEY = "Gurram et al. (2024)"
KINE2GO = "Kine2Go dataset"
SDK = "unitree_sdk2_python"

SLIDES = [
    # ------------------------------------------------------------------ 0
    {
        "key": "title",
        "title": config.PRESENTATION_TITLE,
        "subtitle": "Why each source matters for our crime-scene Unitree Go2",
        "notes": (
            "Introduce myself and the project: a Unitree Go2 robot dog that investigates crime scenes. "
            "It reads bloodstain patterns, decides which areas are interesting, walks there, and estimates where "
            "the victim was, where the attacker stood, and where the weapon was dropped. Today I go through my four "
            "Readings 5 sources and use a small live demo for each one to show why it matters for that project."
        ),
    },
    # ------------------------------------------------------------------ 1
    {
        "key": "pipeline",
        "title": "The Project in One Picture",
        "points": [
            "Train in simulation, deploy on the real Go2.",
            "A high-level investigation policy sends velocity commands to the dog.",
            "The dog's locomotion has to work on real floors: wet, carpeted, cluttered.",
            "Each stage is backed by one or more of the four sources (colour tags).",
        ],
        "notes": (
            "This is the roadmap for the talk. The pipeline goes from a crime-scene simulation, to RL training, to "
            "sim-to-real transfer, to the real Go2 through the SDK. The colour tags show which source supports each "
            "stage. Hwangbo and the survey cover the simulation-to-reality problem, Kine2Go gives ready-made motions "
            "for the Go2, and the Unitree SDK is where the trained policy actually reaches the robot."
        ),
    },
    # ------------------------------------------------------------------ 2
    {
        "key": "hwangbo",
        "source": HWANGBO,
        "title": "Hwangbo: Why a Perfect Simulator Isn't Enough",
        "points": [
            "Problem: hand-tuned controllers take months; RL on a real robot is slow, expensive and risky; "
            "simulation-trained policies usually fail on hardware (the \"reality gap\").",
            "ANYmal: ~32 kg quadruped with 12 series-elastic actuators that are very hard to model analytically.",
            "Hybrid simulator: rigid-body physics (randomized inertial properties) + a learned actuator network.",
            "Actuator network: small MLP predicting torque from a short history of position errors and "
            "velocities, trained on ~4 minutes of real robot data.",
            "Policy (TRPO) outputs joint position targets -> PD controller -> torque; curriculum on penalties; "
            "noise on velocity observations; bounded tanh activation.",
            "Zero-shot transfer: weights copied to the robot with no fine-tuning.",
            "Results: better velocity tracking than the best model-based controller with less torque and power; "
            "~1.5 m/s (25% faster than the previous record); fall recovery in all 9 hardware trials.",
            "Ablation: with an ideal or hand-tuned analytical actuator model, policies could not take a single "
            "step on the real robot.",
        ],
        "demo_title": "Live demo: a toy actuator network",
        "demo_caption": (
            "TOY MODEL. A synthetic 'real' actuator with a series-elastic spring lag, a communication delay, "
            "friction and a torque limit is logged for 3 minutes. A small MLP learns torque from a short history "
            "of position error and velocity. None of these numbers come from the paper."
        ),
        "why": [
            "A policy trained on an idealized Go2 could fail on the real dog, just like the ideal-actuator "
            "policies in the ablation.",
            "We may need logged Go2 motor data (position, velocity, estimated torque from the SDK's LowState) "
            "to learn a model of its actuators.",
        ],
        "notes": (
            "The main lesson from Hwangbo et al. is that you do not need a perfect physics model. They kept the easy "
            "parts (rigid links and contacts) as physics and learned only the hard part, the actuators. In the demo, "
            "the toy actuator hides a delay and a spring lag. The ideal model ignores both, the analytical model "
            "guesses the lag but misses the delay and friction, and the learned network sees a short history so it "
            "can pick up the delay. Move the delay slider and watch the ideal model's error grow. For our dog this "
            "means a policy trained on an idealized Go2 could fail, so logging real Go2 motor data through the SDK "
            "could be needed."
        ),
    },
    # ------------------------------------------------------------------ 3
    {
        "key": "survey",
        "source": SURVEY,
        "title": "Survey: The Toolbox for Crossing the Reality Gap",
        "points": [
            "Basic loop: state (orientation, velocities, joint angles) -> policy -> joint position targets -> "
            "low-level PD controller -> torque. Trained in Isaac Gym or RaiSim from a URDF.",
            "Teacher-student (privileged learning): a teacher uses simulation-only info (contact forces, terrain); "
            "a student imitates it with real sensors only.",
            "RMA (Rapid Motor Adaptation): estimates hidden environment properties from recent states and actions.",
            "Curriculum learning and domain randomization of terrain, friction, motor strength and gains.",
            "Gait-bound (built-in gaits like trotting) vs. gait-free (policy finds its own gait).",
            "Reward design and policy-gradient methods such as PPO; most of the 13 compared works use PPO and "
            "Unitree robots.",
            "Future directions: exteroceptive sensing, model-based + model-free, online learning on the real robot.",
        ],
        "demo_title": "Live demo: domain randomization on a toy push-cart",
        "demo_caption": (
            "TOY MODEL. A 1-D cart must move 1 m and stop inside +/-5 cm. A PD controller with friction "
            "compensation is tuned by quick random search, once on a single nominal floor (fixed) and once across "
            "randomized friction, mass and motor strength (randomized). Simulated results only."
        ),
        "why": [
            "Crime scenes have unknown floors: blood is slippery, carpet adds friction, debris shifts the load, "
            "so the locomotion policy must be trained with randomization.",
            "The survey's call for exteroceptive sensing is exactly what our stain-reading camera adds.",
        ],
        "notes": (
            "The survey is a map of how the field closes the reality gap. Hwangbo made the simulator more realistic; "
            "later work mostly makes the policy tolerant of the remaining gap with domain randomization, "
            "teacher-student training and RMA. In the demo the fixed controller is tuned for one floor and looks "
            "great there, but on carpet-like friction or a heavier load it fails. The randomized controller gives up "
            "a little speed but succeeds on far more floors. Try the sliders to break the fixed controller. Note it "
            "can still fail far outside the randomization range, which is why the ranges must cover real scenes."
        ),
    },
    # ------------------------------------------------------------------ 4
    {
        "key": "kine2go",
        "source": KINE2GO,
        "title": "Kine2Go: A Ready-Made Motion Library for the Go2",
        "points": [
            "40 reference clips: 15 dog motion-capture, 7 synthetic dog (AI4Animation), 12 horse (Vienna Horse "
            "Data Collection), 6 from the Solo8 robot.",
            "Each clip retargeted to the Go2's 12 joints; a PPO imitation policy per clip, trained in the "
            "Genesis simulator with rsl_rl.",
            "20 perturbed rollouts per clip = 800 rollouts, logged at 60 Hz.",
            "Logs: joint positions and velocities, base position, orientation quaternion, linear and angular "
            "velocity, the 12 actions, link poses (metres and radians). motion.npy has shape (T, 61).",
            "About 31 GB; built for behavioral foundation models, with behavioral cloning and retargeting "
            "evaluation as secondary uses.",
            "Simulation only: it does not close the sim-to-real gap by itself.",
        ],
        "demo_title": "Live demo: inside one motion file",
        "demo_caption": (
            "The app lists the Hugging Face repo, downloads ONE motion.npy (never the full dataset) and plots it. "
            "If the download fails it falls back to a bundled SYNTHETIC trot that is not Kine2Go data. Only the "
            "(T, 61) shape, 60 Hz and the foot columns 36:48 come from my notes; other column meanings are assumed."
        ),
        "why": [
            "Slow, careful search gaits and sniffing-style motions could be imitated from the dog clips instead "
            "of being designed by hand.",
            "But it is simulation data, so it still needs the Slide 3 techniques (randomization, adaptation) "
            "before running on a real Go2.",
        ],
        "notes": (
            "Kine2Go is basically the training pipeline from both papers run 40 times: a PPO policy in simulation per "
            "clip, on a Unitree Go2. Its logged fields line up with the observation and action spaces from the "
            "readings. Every policy is told what motion to make by a reference clip, so the gait comes from data "
            "rather than from the reward. For us, the dog clips are a source of careful search and sniffing motions. "
            "Be clear in the demo whether the real file loaded or the synthetic fallback is shown."
        ),
    },
    # ------------------------------------------------------------------ 5
    {
        "key": "sdk",
        "source": SDK,
        "title": "Unitree SDK: Where the Policy Meets the Real Dog",
        "points": [
            "Official Python interface; DDS (CycloneDDS) publish/subscribe on named topics over Ethernet.",
            "High level: SportClient with StandUp, BalanceStand, RecoveryStand and Move(vx, vy, vyaw) for "
            "Unitree's own walking controller.",
            "Low level: subscribe to LowState (IMU quaternion, gyroscope, accelerometer, roll/pitch/yaw; per-motor "
            "position, velocity, estimated torque, temperature; foot forces; battery).",
            "Publish LowCmd: per-motor target position q, target velocity dq, feed-forward torque tau, gains kp, kd.",
            "Turn sport mode off first (MotionSwitcherClient) so two controllers don't fight; the Go2 stand "
            "example sends commands every 2 ms.",
            "Safety steps: clear the area, use low gains, switch off the built-in controller.",
        ],
        "demo_title": "Live demo: a mock SDK (no hardware, no network)",
        "demo_caption": (
            "mock_unitree.py copies the SHAPE of the SDK's API (SportClient.Move, LowState, LowCmd) without "
            "CycloneDDS. (a) A policy loop reads LowState, builds an observation, runs a tiny RANDOM network and "
            "writes q targets into LowCmd. (b) A synthetic stain map drives Move(vx, vy, vyaw) commands."
        ),
        "why": [
            "This is exactly how the investigation policy reaches the real Go2: high-level Move(vx, vy, vyaw) "
            "commands, or a learned gait writing q targets into LowCmd.",
            "LowState also gives the motor data we would log to model the Go2's actuators (Slide 2).",
        ],
        "notes": (
            "The SDK is where deployment happens, which the primary reading covers in about one sentence. LowState "
            "lines up with the observations an RL policy needs and LowCmd's position target plus kp and kd is where "
            "a policy's output goes. The primary reading ran its policy at 200 Hz while the stand example writes "
            "commands every 2 ms, so the policy would run slower while the motors track the latest target, which is "
            "what the mock loop shows. The investigation layer uses the high-level Move command. This app never "
            "sends anything to real hardware."
        ),
    },
    # ------------------------------------------------------------------ 6
    {
        "key": "summary",
        "title": "How the Four Sources Fit Together",
        "table_header": ["Source", "What it gives us", "Project stage", "Risk it addresses"],
        "table": [
            [HWANGBO, "Hybrid simulator idea: learned actuator network + PD position targets",
             "Simulation + sim-to-real", "Policy fails on the real Go2's actuators"],
            [SURVEY, "Toolbox: domain randomization, teacher-student, RMA, PPO, curriculum",
             "RL training", "Unknown floors (wet, carpet, debris)"],
            [KINE2GO, "800 simulated Go2 rollouts from 40 dog/horse/robot clips",
             "Motion priors for training", "Hand-designing careful search gaits"],
            [SDK, "SportClient.Move and LowState/LowCmd over DDS",
             "Deployment on the real Go2", "Unsafe or mismatched deployment"],
        ],
        "next_steps": [
            "Build the crime-scene simulation (stain patterns, varied floors, a Go2 model).",
            "Train the locomotion and investigation policies with domain randomization.",
            "Log real Go2 motor data through LowState to check (or learn) the actuator model.",
            "Deploy through the SDK with safety limits: clear area, low gains, sport mode handled correctly.",
        ],
        "notes": (
            "The four sources cover the whole pipeline. Hwangbo shows how to make the simulator realistic enough, the "
            "survey gives the tools to make the policy robust, Kine2Go gives a motion library for the exact robot we "
            "use, and the SDK is the bridge to the hardware. The next steps follow the pipeline from left to right."
        ),
    },
    # ------------------------------------------------------------------ 7
    {
        "key": "references",
        "title": "References",
        "refs": [
            "Gurram, M., Uttam, P. K., & Ohol, S. S. (2024). Reinforcement learning for quadrupedal locomotion: "
            "Current advancements and future perspectives [Preprint]. arXiv. https://arxiv.org/abs/2410.10438v1",
            "Hwangbo, J., Lee, J., Dosovitskiy, A., Bellicoso, D., Tsounis, V., Koltun, V., & Hutter, M. (2019). "
            "Learning agile and dynamic motor skills for legged robots. Science Robotics. "
            "https://arxiv.org/abs/1901.08652",
            "MIMUW Robotics. (n.d.). Kine2Go: Kinematic dataset for the Unitree Go2 robot with diverse gaits and "
            "motions [Data set]. Hugging Face. https://huggingface.co/datasets/MIMUW-Robotics/kine2go",
            "Unitree Robotics. (n.d.). unitree_sdk2_python [Computer software]. GitHub. "
            "https://github.com/unitreerobotics/unitree_sdk2_python",
        ],
        "notes": "APA references for the four sources, in alphabetical order.",
    },
]

SLIDE_TITLES = [s["title"] for s in SLIDES]
