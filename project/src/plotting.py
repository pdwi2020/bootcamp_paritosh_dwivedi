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


def plot_uncertainty(
    predictions: pd.DataFrame,
    uncertainty: dict,
    output_dir: Path,
) -> Path:
    """Two-panel uncertainty figure: metric error bars, and interval scenarios.

    Left panel answers "how precisely do we know the score" with 95% bootstrap
    error bars. Right panel answers "where might a new observation land" and
    contrasts the empirical and gaussian prediction intervals side by side, which
    is the Stage 11 scenario comparison.
    """

    ridge = uncertainty["ridge_mae_bootstrap_ci"]
    baseline = uncertainty["baseline_mae_bootstrap_ci"]
    scenarios = uncertainty["prediction_interval_scenarios"]
    empirical = scenarios["empirical_residual_percentiles"]
    gaussian = scenarios["gaussian_approximation"]

    fig, (left, right) = plt.subplots(1, 2, figsize=(12, 4.6))

    # --- left: MAE with 95% bootstrap error bars -------------------------
    labels = ["Ridge", "Recent-volatility\nbaseline"]
    centres = [ridge["point_estimate"], baseline["point_estimate"]]
    lower = [c - d["ci_low"] for c, d in zip(centres, (ridge, baseline), strict=True)]
    upper = [d["ci_high"] - c for c, d in zip(centres, (ridge, baseline), strict=True)]
    left.errorbar(
        labels,
        centres,
        yerr=[lower, upper],
        fmt="o",
        color=BLUE,
        ecolor=GRAY,
        elinewidth=2,
        capsize=8,
        markersize=9,
    )
    for x, centre in enumerate(centres):
        left.annotate(
            f"{centre:.4f}",
            (x, centre),
            textcoords="offset points",
            xytext=(12, 0),
            color=BLACK,
            fontsize=9,
        )
    left.set_title("Holdout MAE with 95% bootstrap interval", color=BLACK)
    left.set_ylabel("Mean absolute error (annualised volatility)")
    left.set_xlabel("Model")
    left.grid(axis="y", alpha=0.3)

    # --- right: residuals with both interval scenarios -------------------
    residuals = predictions["actual_next_five_day_vol"] - predictions["ridge_predicted_vol"]
    right.hist(residuals, bins=60, color=LIGHT_BLUE, edgecolor="white")
    for bound, style, colour, name in (
        (empirical["lower_offset"], "-", RED, "Empirical 95%"),
        (empirical["upper_offset"], "-", RED, None),
        (gaussian["lower_offset"], "--", BLACK, "Gaussian 95%"),
        (gaussian["upper_offset"], "--", BLACK, None),
    ):
        right.axvline(bound, linestyle=style, color=colour, linewidth=1.6, label=name)
    right.set_title("Residuals and two prediction-interval scenarios", color=BLACK)
    right.set_xlabel("Actual minus predicted (annualised volatility)")
    right.set_ylabel("Holdout forecast windows")
    right.legend(frameon=False, fontsize=9)
    right.grid(axis="y", alpha=0.3)

    fig.suptitle(
        "Uncertainty: the bootstrap intervals do not overlap, and the gaussian "
        "scenario understates the upper tail",
        fontsize=10,
        color=GRAY,
    )
    fig.tight_layout()
    return _finish(fig, output_dir / "uncertainty_intervals.png")


def create_all_figures(
    feature_frame: pd.DataFrame,
    predictions: pd.DataFrame,
    output_dir: Path,
    *,
    threshold: float,
    ticker: str,
    uncertainty: dict | None = None,
) -> list[Path]:
    """Generate every final project figure."""

    figures = [
        plot_price_and_drawdown(feature_frame, output_dir, ticker),
        plot_volatility_and_threshold(feature_frame, output_dir, threshold, ticker),
        plot_regression_predictions(predictions, output_dir, ticker),
        plot_return_distribution(feature_frame, output_dir, ticker),
        plot_confusion_matrix(predictions, output_dir),
    ]
    if uncertainty is not None:
        figures.append(plot_uncertainty(predictions, uncertainty, output_dir))
    return figures
