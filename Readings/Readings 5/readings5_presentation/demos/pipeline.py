"""
pipeline.py - Slide 1: the project pipeline diagram, with every stage tagged
by the source(s) that support it.
"""
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

import config
from content import HWANGBO, KINE2GO, SDK, SURVEY
from demos.style import plt

STAGES = [
    ("Crime-scene\nsimulation", "stain patterns, varied floors,\nGo2 model, motion priors", [HWANGBO, KINE2GO]),
    ("RL training", "PPO, curriculum,\ndomain randomization", [SURVEY, KINE2GO]),
    ("Sim-to-real\ntransfer", "actuator network,\nrandomization, adaptation", [HWANGBO, SURVEY]),
    ("Real Go2\nvia SDK", "Move(vx, vy, vyaw),\nLowState / LowCmd", [SDK]),
]


def pipeline_figure():
    fig, ax = plt.subplots(figsize=(14, 5.6))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 5.6)
    ax.axis("off")
    w, h, y = 2.8, 1.9, 2.6
    xs = [0.3 + i * 3.45 for i in range(4)]
    for i, (x, (name, sub, sources)) in enumerate(zip(xs, STAGES)):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05,rounding_size=0.15",
                                    fc=config.NAVY, ec="none"))
        ax.text(x + w / 2, y + h - 0.55, name, ha="center", va="center", color="white",
                fontsize=17, fontweight="bold")
        ax.text(x + w / 2, y + 0.45, sub, ha="center", va="center", color="#C9D6E8", fontsize=11.5)
        for j, src in enumerate(sources):
            ty = y - 0.45 - j * 0.62
            ax.add_patch(FancyBboxPatch((x + 0.1, ty - 0.22), w - 0.2, 0.44,
                                        boxstyle="round,pad=0.02,rounding_size=0.2",
                                        fc=config.SOURCE_COLORS[src], ec="none"))
            ax.text(x + w / 2, ty, src, ha="center", va="center", color="white", fontsize=12.5,
                    fontweight="bold")
        if i < 3:
            ax.add_patch(FancyArrowPatch((x + w + 0.05, y + h / 2), (xs[i + 1] - 0.05, y + h / 2),
                                         arrowstyle="-|>", mutation_scale=28, lw=3, color=config.ACCENT))
    # Runtime loop on the real dog
    ax.text(7.0, 5.25, "Train in simulation  ->  deploy on the real Go2", ha="center",
            fontsize=16, color=config.NAVY, fontweight="bold")
    ax.text(7.0, 0.3, "On the dog: stain camera -> investigation policy -> Move(vx, vy, vyaw) -> "
            "locomotion -> motors (wet, carpeted, cluttered floors)",
            ha="center", fontsize=12.5, color=config.GREY, style="italic")
    return fig


def run():
    return {"figures": {"pipeline": pipeline_figure()}}
