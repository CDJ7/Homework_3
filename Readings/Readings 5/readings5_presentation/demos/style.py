"""
style.py - shared matplotlib styling so every figure matches the slide theme.
"""
import matplotlib

matplotlib.use("Agg")  # no GUI window; figures are rendered to images
import matplotlib.pyplot as plt  # noqa: E402

import config  # noqa: E402

_STYLE = {
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": config.GREY,
    "axes.labelcolor": config.TEXT_DARK,
    "axes.titlecolor": config.NAVY,
    "axes.titleweight": "bold",
    "axes.titlesize": 15,
    "axes.labelsize": 13,
    "axes.grid": True,
    "grid.color": "#DDE3EA",
    "grid.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 11.5,
    "legend.frameon": False,
    "font.size": 13,
    "figure.max_open_warning": 0,
}


def apply_style():
    """Apply the presentation style to matplotlib (safe to call repeatedly)."""
    plt.rcParams.update(_STYLE)


def toy_label(ax, text="TOY MODEL - synthetic data", loc="upper right"):
    """Stamp a clear 'toy / synthetic' label on an axes so nobody mistakes
    the numbers for results from the papers."""
    x, ha = (0.99, "right") if "right" in loc else (0.01, "left")
    y, va = (0.98, "top") if "upper" in loc else (0.02, "bottom")
    ax.text(x, y, text, transform=ax.transAxes, ha=ha, va=va, fontsize=9.5,
            color="white", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", fc=config.ACCENT_3, ec="none", alpha=0.9))


def save_figure(fig, name):
    """Save a figure as PNG into output/figures and return the path."""
    config.FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    path = config.FIGURE_DIR / f"{name}.png"
    fig.savefig(path, dpi=config.FIG_DPI, bbox_inches="tight", facecolor="white")
    return path


apply_style()
