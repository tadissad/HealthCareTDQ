from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def select_best_model(artifacts_dir: str) -> str:
    artifacts = Path(artifacts_dir)
    metrics_path = artifacts / "metrics.json"

    if not metrics_path.exists():
        raise FileNotFoundError(f"Missing file: {metrics_path}")

    with metrics_path.open("r", encoding="utf-8") as f:
        metrics = json.load(f)

    best_name = max(metrics.keys(), key=lambda name: metrics[name]["f1"])
    best_model_src = artifacts / f"model_{best_name.lower()}.keras"
    best_model_dst = artifacts / "model_best.keras"

    if not best_model_src.exists():
        raise FileNotFoundError(f"Model file not found: {best_model_src}")

    shutil.copy2(best_model_src, best_model_dst)

    print(f"Best model: {best_name}")
    print(f"F1 score: {metrics[best_name]['f1']:.4f}")
    print(f"Accuracy: {metrics[best_name]['accuracy']:.4f}")
    print(f"Saved best model to: {best_model_dst}")

    return best_name


def main() -> None:
    parser = argparse.ArgumentParser(description="Select best model by F1 score")
    parser.add_argument("--artifacts", default="artifacts", help="Artifacts directory")
    args = parser.parse_args()

    select_best_model(args.artifacts)


if __name__ == "__main__":
    main()
