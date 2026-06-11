from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

try:
    from generate_user_behavior_data import ACTIONS
    from domain.category import CATEGORIES
except ImportError:  # pragma: no cover - fallback when running inside folder
    from generate_user_behavior_data import ACTIONS
    from category import CATEGORIES


@dataclass
class PreparedData:
    X_train: np.ndarray
    X_test: np.ndarray
    y_train: np.ndarray
    y_test: np.ndarray
    action_to_idx: Dict[str, int]
    category_to_idx: Dict[str, int]
    n_features: int
    n_actions: int


def encode_actions(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    action_to_idx = {action: idx for idx, action in enumerate(ACTIONS)}
    encoded = df.copy()
    encoded["action_idx"] = encoded["action"].map(action_to_idx)
    return encoded, action_to_idx


def encode_categories(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    category_to_idx = {category: idx for idx, category in enumerate(CATEGORIES)}
    encoded = df.copy()
    encoded["category_idx"] = encoded["category"].map(category_to_idx)
    return encoded, category_to_idx


def _add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    enriched["timestamp"] = pd.to_datetime(enriched["timestamp"])

    hours = enriched["timestamp"].dt.hour.astype(float)
    day_of_week = enriched["timestamp"].dt.dayofweek.astype(float)

    enriched["hour_sin"] = np.sin(2 * np.pi * hours / 24.0)
    enriched["hour_cos"] = np.cos(2 * np.pi * hours / 24.0)
    enriched["dow_sin"] = np.sin(2 * np.pi * day_of_week / 7.0)
    enriched["dow_cos"] = np.cos(2 * np.pi * day_of_week / 7.0)
    return enriched


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["price_norm"] = (out["price"] - out["price"].min()) / (out["price"].max() - out["price"].min() + 1e-8)
    out["duration_norm"] = (
        (out["session_duration"] - out["session_duration"].min())
        / (out["session_duration"].max() - out["session_duration"].min() + 1e-8)
    )
    out["rating_filled"] = out["rating"].fillna(0.0).astype(float)
    out["rating_norm"] = out["rating_filled"] / 5.0
    return out


def create_sequences(df: pd.DataFrame, seq_len: int = 5) -> Tuple[np.ndarray, np.ndarray]:
    X, y = [], []
    action_eye = np.eye(len(ACTIONS), dtype=np.float32)
    category_eye = np.eye(len(CATEGORIES), dtype=np.float32)

    grouped = df.sort_values(["user_id", "timestamp"]).groupby("user_id")
    for _, user_df in grouped:
        action_idx = user_df["action_idx"].to_numpy(dtype=np.int64)
        category_idx = user_df["category_idx"].to_numpy(dtype=np.int64)

        numeric_features = user_df[
            [
                "price_norm",
                "duration_norm",
                "rating_norm",
                "hour_sin",
                "hour_cos",
                "dow_sin",
                "dow_cos",
            ]
        ].to_numpy(dtype=np.float32)

        action_one_hot = action_eye[action_idx]
        category_one_hot = category_eye[category_idx]
        feature_matrix = np.concatenate([action_one_hot, category_one_hot, numeric_features], axis=1)

        if len(feature_matrix) <= seq_len:
            continue

        for i in range(len(feature_matrix) - seq_len):
            X.append(feature_matrix[i : i + seq_len])
            y.append(int(action_idx[i + seq_len]))

    return np.asarray(X, dtype=np.float32), np.asarray(y, dtype=np.int64)


def prepare_data(csv_path: str, seq_len: int = 5, test_size: float = 0.2, random_state: int = 42) -> PreparedData:
    df = pd.read_csv(csv_path)

    df, action_to_idx = encode_actions(df)
    df, category_to_idx = encode_categories(df)
    df = _add_time_features(df)
    df = _normalize_columns(df)

    X, y = create_sequences(df, seq_len=seq_len)
    if len(X) == 0:
        raise ValueError("No training sequences were created. Check input data and seq_len.")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    return PreparedData(
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test,
        action_to_idx=action_to_idx,
        category_to_idx=category_to_idx,
        n_features=X.shape[-1],
        n_actions=len(action_to_idx),
    )
