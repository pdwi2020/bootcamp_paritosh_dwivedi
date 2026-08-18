"""Presentation-quality analytical figures for the project report."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import confusion_matrix

BLUE = "#2563EB"
LIGHT_BLUE = "#60A5FA"
RED = "#DC2626"
GRAY = "#6B7280"
BLACK = "#111827"


def _finish(fig: plt.Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def plot_price_and_drawdown(frame: pd.DataFrame, output_dir: Path, ticker: str) -> Path:
    """Plot adjusted price and drawdown as stakeholder context."""

    fig, axes = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True, height_ratios=[2, 1])
    axes[0].plot(frame["date"], frame["adjusted_close"], color=BLUE, linewidth=1.6)
    axes[0].set_title(f"{ticker} adjusted close and drawdown")
    axes[0].set_ylabel("Adjusted close ($)")
    axes[1].fill_between(frame["date"], frame["drawdown"], 0, color=RED, alpha=0.35)
    axes[1].plot(frame["date"], frame["drawdown"], color=RED, linewidth=1.0)
    axes[1].set_ylabel("Drawdown")
    axes[1].set_xlabel("Date")
    axes[1].yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    for axis in axes:
        axis.grid(axis="y", alpha=0.2)
        axis.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return _finish(fig, output_dir / "price_and_drawdown.png")


def plot_volatility_and_threshold(
    frame: pd.DataFrame, output_dir: Path, threshold: float, ticker: str
) -> Path:
    """Plot observed rolling volatility and the training-derived risk threshold."""

    recent = frame.tail(756)
    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.plot(recent["date"], recent["rolling_vol_20"], color=BLUE, label="20-day volatility")
    ax.plot(
        recent["date"],
        recent["target_next_week_vol"],
        color=LIGHT_BLUE,
        alpha=0.65,
        label="Next-five-session realized volatility",
    )
    ax.axhline(threshold, color=RED, linestyle="--", label="Elevated-risk threshold")
    ax.set_title(f"{ticker} volatility context (latest three trading years)")
    ax.set_ylabel("Annualized volatility")
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.grid(axis="y", alpha=0.2)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, ncol=3, loc="upper left")
    fig.tight_layout()
    return _finish(fig, output_dir / "volatility_and_risk_threshold.png")


def plot_regression_predictions(predictions: pd.DataFrame, output_dir: Path, ticker: str) -> Path:
    """Compare Ridge predictions with realized volatility and the recent-vol baseline."""

    recent = predictions.tail(504)
    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.plot(
        recent["date"],
        recent["actual_next_five_day_vol"],
        color=BLACK,
        linewidth=1.2,
        label="Actual next-five-session volatility",
    )
    ax.plot(
        recent["date"],
        recent["ridge_predicted_vol"],
        color=BLUE,
        linewidth=1.2,
        label="Ridge prediction",
    )
    ax.plot(
        recent["date"],
        recent["recent_vol_baseline"],
        color=GRAY,
        linewidth=1.0,
        alpha=0.75,
        label="Recent-volatility baseline",
    )
    ax.set_title(f"{ticker} out-of-sample volatility predictions")
    ax.set_ylabel("Annualized volatility")
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.grid(axis="y", alpha=0.2)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, ncol=3, loc="upper left")
    fig.tight_layout()
    return _finish(fig, output_dir / "regression_predictions.png")


def plot_return_distribution(frame: pd.DataFrame, output_dir: Path, ticker: str) -> Path:
    """Plot daily-return distribution with retained tail observations."""

    returns = frame["daily_return"].dropna()
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.hist(returns, bins=100, color=BLUE, alpha=0.82)
    ax.axvline(returns.quantile(0.01), color=RED, linestyle="--", label="1st percentile")
    ax.axvline(returns.quantile(0.99), color=RED, linestyle="--", label="99th percentile")
    ax.set_title(f"{ticker} daily returns retain financially relevant tails")
    ax.set_xlabel("Daily return")
    ax.set_ylabel("Observations")
    ax.xaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.grid(axis="y", alpha=0.2)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False)
    fig.tight_layout()
    return _finish(fig, output_dir / "return_distribution.png")


def plot_confusion_matrix(predictions: pd.DataFrame, output_dir: Path) -> Path:
    """Plot the elevated-risk classification confusion matrix."""

    matrix = confusion_matrix(
        predictions["actual_elevated_risk"],
        predictions["predicted_elevated_risk"],
        labels=[0, 1],
    )
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    image = ax.imshow(matrix, cmap="Blues")
    for row in range(2):
        for column in range(2):
            ax.text(column, row, str(matrix[row, column]), ha="center", va="center", fontsize=16)
    ax.set_xticks([0, 1], ["Normal", "Elevated"])
    ax.set_yticks([0, 1], ["Normal", "Elevated"])
    ax.set_xlabel("Predicted risk")
    ax.set_ylabel("Actual risk")
    ax.set_title("Out-of-sample elevated-risk classification")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    return _finish(fig, output_dir / "classification_confusion_matrix.png")


def create_all_figures(
    feature_frame: pd.DataFrame,
    predictions: pd.DataFrame,
    output_dir: Path,
    *,
    threshold: float,
    ticker: str,
) -> list[Path]:
    """Generate every final project figure."""

    return [
        plot_price_and_drawdown(feature_frame, output_dir, ticker),
        plot_volatility_and_threshold(feature_frame, output_dir, threshold, ticker),
        plot_regression_predictions(predictions, output_dir, ticker),
        plot_return_distribution(feature_frame, output_dir, ticker),
        plot_confusion_matrix(predictions, output_dir),
    ]
