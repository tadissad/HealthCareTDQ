from __future__ import annotations


def _require_tensorflow() -> None:
    try:
        import tensorflow  # noqa: F401
    except Exception as exc:
        raise ImportError(
            "TensorFlow is required. Install it with: pip install tensorflow"
        ) from exc


def build_rnn_model(seq_len: int, n_features: int, n_actions: int):
    _require_tensorflow()
    from tensorflow.keras.layers import Dense, Dropout, Input, LSTM, SimpleRNN
    from tensorflow.keras.models import Sequential

    model = Sequential(
        [
            Input(shape=(seq_len, n_features)),
            LSTM(64, return_sequences=True),
            Dropout(0.2),
            SimpleRNN(32),
            Dropout(0.2),
            Dense(16, activation="relu"),
            Dense(n_actions, activation="softmax"),
        ]
    )
    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
    return model


def build_lstm_model(seq_len: int, n_features: int, n_actions: int):
    _require_tensorflow()
    from tensorflow.keras.layers import Dense, Dropout, Input, LSTM
    from tensorflow.keras.models import Sequential

    model = Sequential(
        [
            Input(shape=(seq_len, n_features)),
            LSTM(128, return_sequences=True),
            Dropout(0.3),
            LSTM(64),
            Dropout(0.3),
            Dense(32, activation="relu"),
            Dense(n_actions, activation="softmax"),
        ]
    )
    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
    return model


def build_bilstm_model(seq_len: int, n_features: int, n_actions: int):
    _require_tensorflow()
    from tensorflow.keras.layers import Bidirectional, Dense, Dropout, Input, LSTM
    from tensorflow.keras.models import Sequential

    model = Sequential(
        [
            Input(shape=(seq_len, n_features)),
            Bidirectional(LSTM(128, return_sequences=True)),
            Dropout(0.3),
            Bidirectional(LSTM(64)),
            Dropout(0.3),
            Dense(32, activation="relu"),
            Dense(n_actions, activation="softmax"),
        ]
    )
    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
    return model
