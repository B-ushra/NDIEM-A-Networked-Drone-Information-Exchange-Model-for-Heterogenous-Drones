"""
make_figures.py
====================================================================
Generates the ablation and latency figures from the frozen results
reported in the paper. Values are hardcoded to match the tables so
the figures and tables cannot drift.

Produces (300 DPI, PNG + PDF):
  ablation_figure.{png,pdf}     ablation study (clean condition)
  latency_figure.{png,pdf}      transformation / end-to-end / overhead

Usage:
  python make_figures.py
"""

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({"font.size": 12, "figure.dpi": 300})


# ---------------------------------------------------------------------
# ABLATION FIGURE  (clean condition)
# ---------------------------------------------------------------------
def ablation_figure():
    configs = ["Full\nNDIEM+XML", "No\nValidator", "No XML\nSchema",
               "No Message\nBus", "Degraded\nMapping"]
    interop    = [100.0, 100.0,   0.0, 100.0, 100.0]
    integrity  = [100.0, 100.0, 91.78, 100.0,  69.93]
    validation = [100.0, None,  None, 100.0, 100.0]      # None -> N/A
    latency    = [0.0445, 0.0386, 0.0022, 0.0421, 0.0413]

    x = np.arange(len(configs)); w = 0.25
    BLUE, ORANGE, GREEN, LINE = "#1f77b4", "#ff7f0e", "#2ca02c", "#17384f"
    fig, ax1 = plt.subplots(figsize=(9, 5))

    def draw(vals, off, color, label):
        heights = [v if v is not None else 0 for v in vals]
        ax1.bar(x + off, heights, w, color=color, label=label)
        for xi, v in zip(x + off, vals):
            if v is None:
                ax1.text(xi, 2, "N/A", ha="center", va="bottom",
                         fontsize=8, rotation=90, color="gray")
            else:
                ax1.text(xi, v + 1.5, f"{v:g}", ha="center", fontsize=8)

    draw(interop,    -w, BLUE,   "Interoperability (%)")
    draw(integrity,   0, ORANGE, "Data Integrity (%)")
    draw(validation,  w, GREEN,  "Validation (%)")

    ax1.set_ylabel("Percentage (%)"); ax1.set_ylim(0, 122)
    ax1.set_xticks(x); ax1.set_xticklabels(configs)
    ax1.set_title("Ablation Study of NDIEM Components", fontweight="bold")

    ax2 = ax1.twinx()
    ax2.plot(x, latency, color=LINE, marker="o", lw=2, label="End-to-End Latency (ms)")
    for xi, v in zip(x, latency):
        ax2.annotate(f"{v:.4f}", (xi, v), textcoords="offset points",
                     xytext=(0, 14), ha="center", fontsize=8, color=LINE,
                     fontweight="bold",
                     bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))
    ax2.set_ylabel("End-to-End Latency (ms)", color=LINE)
    ax2.set_ylim(0, max(latency) * 1.9)
    ax2.tick_params(axis="y", labelcolor=LINE)

    l1, lab1 = ax1.get_legend_handles_labels()
    l2, lab2 = ax2.get_legend_handles_labels()
    ax1.legend(l1 + l2, lab1 + lab2, loc="upper center", framealpha=0.95,
               fontsize=9, ncol=2)
    ax1.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig("ablation_figure.png", dpi=300, bbox_inches="tight")
    fig.savefig("ablation_figure.pdf", bbox_inches="tight")
    plt.close(fig)
    print("saved ablation_figure.{png,pdf}")


# ---------------------------------------------------------------------
# LATENCY FIGURE
# ---------------------------------------------------------------------
def latency_figure():
    platforms  = ["Crazyflie", "Hexacopter", "Tello EDU"]
    transform  = [0.049, 0.057, 0.073]
    end_to_end = [0.062, 0.072, 0.092]
    overhead   = [0.013, 0.015, 0.019]

    x = np.arange(len(platforms)); w = 0.25
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x - w, transform,  w, color="#1f77b4", label="Transformation Latency (ms)")
    ax.bar(x,     end_to_end, w, color="#ff7f0e", label="End-to-End Processing Time (ms)")
    ax.bar(x + w, overhead,   w, color="#2ca02c", label="Overhead (ms)")

    for off, vals in [(-w, transform), (0, end_to_end), (w, overhead)]:
        for xi, v in zip(x + off, vals):
            ax.text(xi, v + 0.002, f"{v:.3f}", ha="center", fontsize=9)

    ax.set_ylabel("Latency (ms)"); ax.set_xlabel("UAV Platform")
    ax.set_xticks(x); ax.set_xticklabels(platforms)
    ax.set_ylim(0, 0.105)
    ax.set_title("Transformation, End-to-End, and Overhead Latency of NDIEM",
                 fontweight="bold")
    ax.legend(framealpha=0.9, fontsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig("latency_figure.png", dpi=300, bbox_inches="tight")
    fig.savefig("latency_figure.pdf", bbox_inches="tight")
    plt.close(fig)
    print("saved latency_figure.{png,pdf}")


if __name__ == "__main__":
    ablation_figure()
    latency_figure()
