from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.utils.class_weight import compute_class_weight

try:
    from models import build_bilstm_model, build_lstm_model, build_rnn_model
    from preprocess_data import prepare_data
except ImportError:  # pragma: no cover - fallback when running inside folder
    from models import build_bilstm_model, build_lstm_model, build_rnn_model
    from preprocess_data import prepare_data


def _to_categorical(y: np.ndarray, n_actions: int) -> np.ndarray:
    from tensorflow.keras.utils import to_categorical

    return to_categorical(y, num_classes=n_actions)


def train_all_models(
    data_csv: str,
    output_dir: str,
    seq_len: int = 5,
    epochs: int = 30,
    batch_size: int = 32,
    learning_rate: float = 1e-3,
) -> Dict[str, Dict[str, float]]:
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    from tensorflow.keras.losses import CategoricalCrossentropy
    from tensorflow.keras.optimizers import Adam

    prepared = prepare_data(data_csv, seq_len=seq_len)
    y_train_oh = _to_categorical(prepared.y_train, prepared.n_actions)
    classes = np.unique(prepared.y_train)
    class_weights = compute_class_weight(class_weight="balanced", classes=classes, y=prepared.y_train)
    class_weight_map = {int(cls): float(weight) for cls, weight in zip(classes, class_weights)}

    builders = {
        "RNN": build_rnn_model,
        "LSTM": build_lstm_model,
        "BiLSTM": build_bilstm_model,
    }

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    metrics: Dict[str, Dict[str, float]] = {}
    histories: Dict[str, Dict[str, list]] = {}

    for name, builder in builders.items():
        print(f"\nTraining {name}...")
        model = builder(seq_len, prepared.n_features, prepared.n_actions)
        model.compile(
            optimizer=Adam(learning_rate=learning_rate),
            loss=CategoricalCrossentropy(label_smoothing=0.05),
            metrics=["accuracy"],
        )

        callbacks = [
            EarlyStopping(monitor="val_loss", patience=8, restore_best_weights=True),
            ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=3, min_lr=1e-5, verbose=1),
        ]

        history = model.fit(
            prepared.X_train,
            y_train_oh,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2,
            verbose=1,
            callbacks=callbacks,
            class_weight=class_weight_map,
        )

        probs = model.predict(prepared.X_test, verbose=0)
        y_pred = np.argmax(probs, axis=1)

        metrics[name] = {
            "accuracy": float(accuracy_score(prepared.y_test, y_pred)),
            "precision": float(precision_score(prepared.y_test, y_pred, average="weighted", zero_division=0)),
            "recall": float(recall_score(prepared.y_test, y_pred, average="weighted", zero_division=0)),
            "f1": float(f1_score(prepared.y_test, y_pred, average="weighted", zero_division=0)),
        }

        histories[name] = {k: [float(v) for v in values] for k, values in history.history.items()}

        model_path = output / f"model_{name.lower()}.keras"
        model.save(model_path)
        print(f"Saved {name} model to {model_path}")

    metrics_path = output / "metrics.json"
    history_path = output / "history.json"
    mapping_path = output / "label_mappings.json"

    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    with history_path.open("w", encoding="utf-8") as f:
        json.dump(histories, f, indent=2)

    with mapping_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "action_to_idx": prepared.action_to_idx,
                "category_to_idx": prepared.category_to_idx,
                "n_features": prepared.n_features,
                "n_actions": prepared.n_actions,
                "seq_len": seq_len,
                "learning_rate": learning_rate,
                "class_weight": class_weight_map,
            },
            f,
            indent=2,
        )

    print("\nTraining complete.")
    print(f"Metrics: {metrics_path}")
    print(f"History: {history_path}")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train RNN/LSTM/BiLSTM models")
    parser.add_argument("--data", default="data_user500.csv", help="Path to data_user500.csv")
    parser.add_argument("--output", default="artifacts", help="Output directory")
    parser.add_argument("--seq-len", type=int, default=5, help="Sequence length")
    parser.add_argument("--epochs", type=int, default=30, help="Training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--learning-rate", type=float, default=1e-3, help="Initial learning rate")
    args = parser.parse_args()

    train_all_models(
        data_csv=args.data,
        output_dir=args.output,
        seq_len=args.seq_len,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
    )


if __name__ == "__main__":
    main()
