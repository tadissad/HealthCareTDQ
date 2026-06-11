from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


def plot_comparison(metrics: dict, output_dir: Path) -> None:
    metric_names = ["accuracy", "precision", "recall", "f1"]
    model_names = list(metrics.keys())

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    colors = ["#CC5A71", "#2D87BB", "#6FAF3A"]

    for i, metric in enumerate(metric_names):
        ax = axes[i // 2, i % 2]
        values = [metrics[name][metric] for name in model_names]
        ax.bar(model_names, values, color=colors[: len(model_names)])
        ax.set_title(f"{metric.upper()} Comparison")
        ax.set_ylim(0, 1)
        ax.set_ylabel(metric)

    fig.tight_layout()
    output_path = output_dir / "model_comparison.png"
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"Saved comparison chart: {output_path}")


def plot_training_history(history_data: dict, output_dir: Path) -> None:
    model_names = list(history_data.keys())
    fig, axes = plt.subplots(1, len(model_names), figsize=(5 * len(model_names), 4))

    if len(model_names) == 1:
        axes = [axes]

    for idx, model_name in enumerate(model_names):
        history = history_data[model_name]
        ax = axes[idx]
        ax.plot(history.get("accuracy", []), label="Train Acc")
        ax.plot(history.get("val_accuracy", []), label="Val Acc")
        ax.set_title(f"{model_name} Training")
        ax.set_xlabel("Epoch")
        ax.set_ylabel("Accuracy")
        ax.legend()

    fig.tight_layout()
    output_path = output_dir / "training_history.png"
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"Saved training history chart: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot model comparison and training history")
    parser.add_argument("--artifacts", default="artifacts", help="Artifacts directory")
    args = parser.parse_args()

    artifacts = Path(args.artifacts)
    metrics_path = artifacts / "metrics.json"
    history_path = artifacts / "history.json"

    if not metrics_path.exists() or not history_path.exists():
        raise FileNotFoundError("Run training first to generate metrics.json and history.json")

    with metrics_path.open("r", encoding="utf-8") as f:
        metrics = json.load(f)

    with history_path.open("r", encoding="utf-8") as f:
        history_data = json.load(f)

    plot_comparison(metrics, artifacts)
    plot_training_history(history_data, artifacts)


if __name__ == "__main__":
    main()
