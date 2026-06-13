"""
Prediction of Final Exam Score Using Machine Learning Models
=============================================================
- Version 1: Gradient Boosting Regressor
- Version 2: MLP (GNN-style)
- Version 3: GraphSAGE (GNN)
- Version 4: Random Forest Regressor
- Version 5: Linear Regression

5 Tasks:
  1. Construct dataset with peer influence
  2. Train 5 models
  3. Evaluate using 5 metrics (MAE, MSE, RMSE, MAPE, R²)
  4. Compare under different social structures
  5. Analyze peer influence propagation
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
warnings.filterwarnings("ignore")

np.random.seed(42)
torch.manual_seed(42)


# ╔══════════════════════════════════════════════════════════════╗
# ║  TASK 1: Construct Dataset with Peer Influence              ║
# ╚══════════════════════════════════════════════════════════════╝

def construct_dataset(N=800):
    """
    Construct dataset with 5 academic scores + 10 peer scores.
    Columns 0-4: javaProg, pythonProg, dataStructure, softwareAD, intelligentSysDev
    Columns 5-14: 10 peer scores
    """
    X = np.random.randint(4, 10, size=(N, 15))

    peer_mean = X[:, 5:15].mean(axis=1)
    peer_std = X[:, 5:15].std(axis=1)

    # Final exam = weighted sum of academic + peer influence + noise
    y = (
        0.25 * X[:, 0] +   # javaProg
        0.20 * X[:, 1] +   # pythonProg
        0.10 * X[:, 2] +   # dataStructure
        0.15 * X[:, 3] +   # softwareAD
        0.10 * X[:, 4] +   # intelligentSysDev
        0.15 * peer_mean +  # peer influence (positive)
        -0.05 * peer_std +  # peer diversity (negative)
        np.random.normal(0, 0.25, N)
    )

    # Clip to valid score range [0, 10]
    y = np.clip(y, 0, 10)

    df = pd.DataFrame(X, columns=[
        'javaProg', 'pythonProg', 'dataStructure', 'softwareAD', 'intelligentSysDev',
        'peer1', 'peer2', 'peer3', 'peer4', 'peer5',
        'peer6', 'peer7', 'peer8', 'peer9', 'peer10'
    ])
    df['peer_mean'] = peer_mean
    df['peer_std'] = peer_std
    df['FinalExam'] = y

    return df


# ╔══════════════════════════════════════════════════════════════╗
# ║  MODEL DEFINITIONS                                          ║
# ╚══════════════════════════════════════════════════════════════╝

class GNNStyleMLP(nn.Module):
    """Version 2: MLP (GNN-style) — treats peer features as neighborhood aggregation."""
    def __init__(self, in_dim):
        super().__init__()
        self.fc1 = nn.Linear(in_dim, 64)
        self.fc2 = nn.Linear(64, 32)
        self.out = nn.Linear(32, 1)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.out(x)


class GraphSAGE(nn.Module):
    """Version 3: GraphSAGE GNN — uses adjacency matrix for neighbor aggregation."""
    def __init__(self, in_dim, hidden=64):
        super().__init__()
        self.fc1 = nn.Linear(in_dim * 2, hidden)
        self.fc2 = nn.Linear(hidden, 32)
        self.out = nn.Linear(32, 1)

    def forward(self, x, adj):
        neigh = torch.matmul(adj, x)
        h = torch.cat([x, neigh], dim=1)
        h = F.relu(self.fc1(h))
        h = F.relu(self.fc2(h))
        return self.out(h).squeeze()


# ╔══════════════════════════════════════════════════════════════╗
# ║  TASK 3: Evaluation Metrics                                 ║
# ╚══════════════════════════════════════════════════════════════╝

def compute_metrics(y_true, y_pred):
    """Compute MAE, MSE, RMSE, MAPE, R² — 5 evaluation metrics."""
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)

    # MAPE: avoid division by zero
    mask = y_true != 0
    mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100

    r2 = r2_score(y_true, y_pred)

    return {
        'MAE': round(mae, 4),
        'MSE': round(mse, 4),
        'RMSE': round(rmse, 4),
        'MAPE': round(mape, 2),
        'R2': round(r2, 4)
    }


# ╔══════════════════════════════════════════════════════════════╗
# ║  TASK 2: Train 5 Models                                     ║
# ╚══════════════════════════════════════════════════════════════╝

def train_v1_gboost(df):
    """Version 1: Gradient Boosting Regressor."""
    print("\n" + "=" * 60)
    print("  Version 1: Gradient Boosting Regressor")
    print("=" * 60)

    features = df.drop('FinalExam', axis=1)
    target = df['FinalExam']

    X_train, X_test, y_train, y_test = train_test_split(
        features, target, test_size=0.2, random_state=42
    )

    model = GradientBoostingRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=4,
        random_state=42
    )
    model.fit(X_train, y_train)

    pred_test = model.predict(X_test)
    metrics = compute_metrics(y_test.values, pred_test)

    print(f"  MAE: {metrics['MAE']:.4f}  |  MSE: {metrics['MSE']:.4f}  |  RMSE: {metrics['RMSE']:.4f}")
    print(f"  MAPE: {metrics['MAPE']:.2f}%  |  R²: {metrics['R2']:.4f}")

    return model, features.columns.tolist(), metrics


def train_v2_mlp(df, epochs=300):
    """Version 2: MLP (GNN-style)."""
    print("\n" + "=" * 60)
    print("  Version 2: MLP (GNN-style)")
    print("=" * 60)

    features = df.drop('FinalExam', axis=1)
    target = df['FinalExam']

    X_train, X_test, y_train, y_test = train_test_split(
        features.values, target.values, test_size=0.2, random_state=42
    )

    X_train_t = torch.tensor(X_train, dtype=torch.float32)
    y_train_t = torch.tensor(y_train, dtype=torch.float32).view(-1, 1)
    X_test_t = torch.tensor(X_test, dtype=torch.float32)

    model = GNNStyleMLP(X_train_t.shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    loss_fn = nn.MSELoss()

    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        pred = model(X_train_t)
        loss = loss_fn(pred, y_train_t)
        loss.backward()
        optimizer.step()
        if (epoch + 1) % 100 == 0:
            print(f"    Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}")

    model.eval()
    with torch.no_grad():
        pred_test = model(X_test_t).squeeze().numpy()

    metrics = compute_metrics(y_test, pred_test)

    print(f"  MAE: {metrics['MAE']:.4f}  |  MSE: {metrics['MSE']:.4f}  |  RMSE: {metrics['RMSE']:.4f}")
    print(f"  MAPE: {metrics['MAPE']:.2f}%  |  R²: {metrics['R2']:.4f}")

    return model, features.columns.tolist(), metrics


def train_v3_graphsage(df, epochs=300):
    """Version 3: GraphSAGE GNN."""
    print("\n" + "=" * 60)
    print("  Version 3: GraphSAGE (GNN)")
    print("=" * 60)

    # Use a smaller subset for GraphSAGE (adjacency matrix is N×N)
    N = min(len(df), 300)
    df_sub = df.iloc[:N].copy()

    X_all = df_sub.drop(['FinalExam', 'peer_mean', 'peer_std'], axis=1).values
    X_academic = X_all[:, :5]
    y = df_sub['FinalExam'].values

    X_full = np.hstack([X_all, df_sub[['peer_mean', 'peer_std']].values])
    X_tensor = torch.tensor(X_full, dtype=torch.float32)
    y_tensor = torch.tensor(y, dtype=torch.float32)

    # Build adjacency from academic similarity
    print("    Building adjacency matrix...")
    A = build_adjacency(X_academic, threshold=6.0)

    # Train/test split by indices
    indices = np.arange(N)
    train_idx, test_idx = train_test_split(indices, test_size=0.2, random_state=42)

    model = GraphSAGE(X_tensor.shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    loss_fn = nn.MSELoss()

    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        pred = model(X_tensor, A)
        loss = loss_fn(pred[train_idx], y_tensor[train_idx])
        loss.backward()
        optimizer.step()
        if (epoch + 1) % 100 == 0:
            print(f"    Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}")

    model.eval()
    with torch.no_grad():
        pred_all = model(X_tensor, A).numpy()

    pred_test = pred_all[test_idx]
    y_test = y[test_idx]

    metrics = compute_metrics(y_test, pred_test)

    print(f"  MAE: {metrics['MAE']:.4f}  |  MSE: {metrics['MSE']:.4f}  |  RMSE: {metrics['RMSE']:.4f}")
    print(f"  MAPE: {metrics['MAPE']:.2f}%  |  R²: {metrics['R2']:.4f}")

    return model, A, X_tensor, metrics


def build_adjacency(X_academic, threshold=6.0):
    """Build adjacency matrix based on academic similarity."""
    N = len(X_academic)
    A = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            if i != j:
                sim = np.linalg.norm(X_academic[i] - X_academic[j])
                if sim < threshold:
                    A[i, j] = 1.0
    # Row-normalize
    row_sum = A.sum(axis=1, keepdims=True) + 1e-6
    A = A / row_sum
    return torch.tensor(A, dtype=torch.float32)


def train_v4_random_forest(df):
    """Version 4: Random Forest Regressor."""
    print("\n" + "=" * 60)
    print("  Version 4: Random Forest Regressor")
    print("=" * 60)

    features = df.drop('FinalExam', axis=1)
    target = df['FinalExam']

    X_train, X_test, y_train, y_test = train_test_split(
        features, target, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=6,
        random_state=42
    )
    model.fit(X_train, y_train)

    pred_test = model.predict(X_test)
    metrics = compute_metrics(y_test.values, pred_test)

    print(f"  MAE: {metrics['MAE']:.4f}  |  MSE: {metrics['MSE']:.4f}  |  RMSE: {metrics['RMSE']:.4f}")
    print(f"  MAPE: {metrics['MAPE']:.2f}%  |  R²: {metrics['R2']:.4f}")

    return model, features.columns.tolist(), metrics


def train_v5_linear_regression(df):
    """Version 5: Linear Regression."""
    print("\n" + "=" * 60)
    print("  Version 5: Linear Regression")
    print("=" * 60)

    features = df.drop('FinalExam', axis=1)
    target = df['FinalExam']

    X_train, X_test, y_train, y_test = train_test_split(
        features, target, test_size=0.2, random_state=42
    )

    model = LinearRegression()
    model.fit(X_train, y_train)

    pred_test = model.predict(X_test)
    metrics = compute_metrics(y_test.values, pred_test)

    print(f"  MAE: {metrics['MAE']:.4f}  |  MSE: {metrics['MSE']:.4f}  |  RMSE: {metrics['RMSE']:.4f}")
    print(f"  MAPE: {metrics['MAPE']:.2f}%  |  R²: {metrics['R2']:.4f}")

    return model, features.columns.tolist(), metrics


# ╔══════════════════════════════════════════════════════════════╗
# ║  TASK 4: Compare Under Different Social Structures          ║
# ╚══════════════════════════════════════════════════════════════╝

def compare_social_structures():
    """Compare models under different social structures (peer diversity)."""
    print("\n" + "=" * 60)
    print("  TASK 4: Compare Under Different Social Structures")
    print("=" * 60)

    structures = {
        'Homogeneous (low diversity)': {'peer_range': (6, 8), 'label': 'Homo'},
        'Heterogeneous (high diversity)': {'peer_range': (2, 10), 'label': 'Hetero'},
        'Mixed': {'peer_range': (4, 10), 'label': 'Mixed'},
    }

    results = []
    for name, cfg in structures.items():
        lo, hi = cfg['peer_range']
        N = 500
        X = np.random.randint(4, 10, size=(N, 5))
        peers = np.random.randint(lo, hi, size=(N, 10))
        X_full = np.hstack([X, peers])

        peer_mean = peers.mean(axis=1)
        peer_std = peers.std(axis=1)
        y = (
            0.25 * X[:, 0] + 0.20 * X[:, 1] + 0.10 * X[:, 2] +
            0.15 * X[:, 3] + 0.10 * X[:, 4] +
            0.15 * peer_mean - 0.05 * peer_std +
            np.random.normal(0, 0.25, N)
        )
        y = np.clip(y, 0, 10)

        df_temp = pd.DataFrame(
            np.hstack([X_full, peer_mean.reshape(-1, 1), peer_std.reshape(-1, 1)]),
            columns=[f'f{i}' for i in range(15)] + ['peer_mean', 'peer_std']
        )
        df_temp['FinalExam'] = y

        feats = df_temp.drop('FinalExam', axis=1)
        X_tr, X_te, y_tr, y_te = train_test_split(feats, y, test_size=0.2, random_state=42)

        gb = GradientBoostingRegressor(n_estimators=200, learning_rate=0.05, max_depth=4, random_state=42)
        gb.fit(X_tr, y_tr)
        pred = gb.predict(X_te)
        m = compute_metrics(y_te, pred)
        m['Structure'] = cfg['label']
        m['Peer Std (avg)'] = round(peer_std.mean(), 3)
        results.append(m)

    df_cmp = pd.DataFrame(results)
    print(df_cmp[['Structure', 'Peer Std (avg)', 'MAE', 'RMSE', 'R2']].to_string(index=False))
    return df_cmp


# ╔══════════════════════════════════════════════════════════════╗
# ║  TASK 5: Analyze Peer Influence Propagation                 ║
# ╚══════════════════════════════════════════════════════════════╝

def analyze_peer_influence(model_gb, feature_cols):
    """Analyze how peer scores influence the final prediction."""
    print("\n" + "=" * 60)
    print("  TASK 5: Analyze Peer Influence Propagation")
    print("=" * 60)

    importances = model_gb.feature_importances_
    fi = pd.DataFrame({
        'Feature': feature_cols,
        'Importance': importances
    }).sort_values('Importance', ascending=False)

    academic_imp = fi[fi['Feature'].isin(
        ['javaProg', 'pythonProg', 'dataStructure', 'softwareAD', 'intelligentSysDev']
    )]['Importance'].sum()

    peer_imp = fi[fi['Feature'].str.startswith('peer')]['Importance'].sum()

    print(f"\n  Academic features importance: {academic_imp:.4f} ({academic_imp*100:.1f}%)")
    print(f"  Peer features importance:     {peer_imp:.4f} ({peer_imp*100:.1f}%)")
    print(f"\n  Top features:")
    print(fi.head(10).to_string(index=False))

    # Sensitivity analysis: how much does changing peer scores affect prediction?
    print("\n  Peer Influence Sensitivity Analysis:")
    base = np.array([7, 7, 7, 7, 7] + [7]*10 + [7.0, 0.0]).reshape(1, -1)

    base_pred = model_gb.predict(base)[0]
    print(f"    Base prediction (all 7s): {base_pred:.2f}")

    # Low peers
    low_peer = base.copy()
    low_peer[0, 5:15] = 4
    low_peer[0, 15] = 4.0  # peer_mean
    low_peer[0, 16] = 0.0  # peer_std
    low_pred = model_gb.predict(low_peer)[0]
    print(f"    All peers = 4:            {low_pred:.2f} (Δ = {low_pred - base_pred:+.2f})")

    # High peers
    high_peer = base.copy()
    high_peer[0, 5:15] = 9
    high_peer[0, 15] = 9.0
    high_peer[0, 16] = 0.0
    high_pred = model_gb.predict(high_peer)[0]
    print(f"    All peers = 9:            {high_pred:.2f} (Δ = {high_pred - base_pred:+.2f})")

    print(f"\n  Peer influence range: {high_pred - low_pred:.2f} points")
    print(f"     (Changing peers from 4→9 while keeping academic scores at 7)")


# ╔══════════════════════════════════════════════════════════════╗
# ║  STUDENT INPUT & PREDICTION                                 ║
# ╚══════════════════════════════════════════════════════════════╝

def get_student_input():
    """Get student's 5 academic scores + 10 peer scores."""
    print("\n" + "=" * 60)
    print("  NHẬP ĐIỂM CỦA BẠN")
    print("=" * 60)

    academic_names = ['Java Programming', 'Python Programming',
                      'Data Structure', 'Software Analysis & Design',
                      'Intelligent System Dev']

    print("\n  Nhập 5 điểm môn học (0-10):")
    academic = []
    for name in academic_names:
        while True:
            try:
                val = float(input(f"    {name}: "))
                if 0 <= val <= 10:
                    academic.append(val)
                    break
                print("    Điểm phải từ 0 đến 10!")
            except ValueError:
                print("    Vui lòng nhập số!")

    print("\n  Nhập 10 điểm từ bạn bè (0-10):")
    peers = []
    for i in range(10):
        while True:
            try:
                val = float(input(f"    Peer {i+1}: "))
                if 0 <= val <= 10:
                    peers.append(val)
                    break
                print("    Điểm phải từ 0 đến 10!")
            except ValueError:
                print("    Vui lòng nhập số!")

    return np.array(academic), np.array(peers)


def predict_student_score(academic, peers, model_gb, model_mlp, model_gs, model_rf, model_lr, A, X_gs, feature_cols):
    """Predict student's final exam score using all 5 models."""
    print("\n" + "=" * 60)
    print("  KẾT QUẢ DỰ ĐOÁN TỪ 5 MÔ HÌNH")
    print("=" * 60)

    peer_mean = peers.mean()
    peer_std = peers.std()

    # ── V1: Gradient Boosting ──
    x_gb = np.hstack([academic, peers, [peer_mean, peer_std]]).reshape(1, -1)
    pred_gb = model_gb.predict(x_gb)[0]

    # ── V2: MLP ──
    x_mlp = torch.tensor(x_gb, dtype=torch.float32)
    model_mlp.eval()
    with torch.no_grad():
        pred_mlp = model_mlp(x_mlp).item()

    # ── V3: GraphSAGE ──
    # Add student as new node, connect to most similar existing nodes
    x_new = torch.tensor(
        np.hstack([academic, peers, [peer_mean, peer_std]]),
        dtype=torch.float32
    ).unsqueeze(0)
    X_aug = torch.cat([X_gs, x_new], dim=0)

    N_old = A.shape[0]
    A_aug = torch.zeros(N_old + 1, N_old + 1)
    A_aug[:N_old, :N_old] = A

    # Connect to top-5 most similar nodes
    x_acad_new = academic
    x_acad_old = X_gs[:, :5].numpy()
    dists = np.linalg.norm(x_acad_old - x_acad_new, axis=1)
    top_k = np.argsort(dists)[:5]
    for idx in top_k:
        A_aug[N_old, idx] = 1.0
        A_aug[idx, N_old] = 1.0

    # Re-normalize
    row_sum = A_aug.sum(dim=1, keepdim=True) + 1e-6
    A_aug = A_aug / row_sum

    model_gs.eval()
    with torch.no_grad():
        pred_all = model_gs(X_aug, A_aug)
        pred_gs = pred_all[-1].item()

    # ── V4: Random Forest ──
    pred_rf = model_rf.predict(x_gb)[0]

    # ── V5: Linear Regression ──
    pred_lr = model_lr.predict(x_gb)[0]

    # Print results
    print(f"\n  Điểm của bạn:")
    print(f"     Java: {academic[0]}, Python: {academic[1]}, DS: {academic[2]}, SA&D: {academic[3]}, ISD: {academic[4]}")
    print(f"     Peer mean: {peer_mean:.2f}, Peer std: {peer_std:.2f}")

    print(f"\n  ╔{'═'*50}╗")
    print(f"  ║ {'Model':<25} {'Predicted Score':>20}  ║")
    print(f"  ╠{'═'*50}╣")
    print(f"  ║ {'V1: Gradient Boosting':<25} {pred_gb:>18.2f}  ║")
    print(f"  ║ {'V2: MLP (GNN-style)':<25} {pred_mlp:>18.2f}  ║")
    print(f"  ║ {'V3: GraphSAGE (GNN)':<25} {pred_gs:>18.2f}  ║")
    print(f"  ║ {'V4: Random Forest':<25} {pred_rf:>18.2f}  ║")
    print(f"  ║ {'V5: Linear Regression':<25} {pred_lr:>18.2f}  ║")
    print(f"  ╠{'═'*50}╣")
    print(f"  ║ {'Average (All 5)':<25} {(pred_gb+pred_mlp+pred_gs+pred_rf+pred_lr)/5:>18.2f}  ║")
    print(f"  ╚{'═'*50}╝")

    return pred_gb, pred_mlp, pred_gs, pred_rf, pred_lr


# ╔══════════════════════════════════════════════════════════════╗
# ║  MAIN                                                       ║
# ╚══════════════════════════════════════════════════════════════╝

def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  Prediction of Final Exam Score                      ║")
    print("║  Using Machine Learning Models (5 Versions)             ║")
    print("╚══════════════════════════════════════════════════════════╝")

    # ─── TASK 1: Construct Dataset ───
    print("\nTask 1: Constructing dataset with peer influence...")
    df = construct_dataset(N=800)
    print(f"   Dataset: {len(df)} samples, {df.shape[1]} columns")
    print(f"   Target range: [{df['FinalExam'].min():.2f}, {df['FinalExam'].max():.2f}]")
    print(f"   Target mean:  {df['FinalExam'].mean():.2f}")

    # ─── TASK 2: Train 5 Models ───
    print("\nTask 2: Training 5 models...")

    model_gb, feat_cols, metrics_gb = train_v1_gboost(df)
    model_mlp, _, metrics_mlp = train_v2_mlp(df, epochs=300)
    model_gs, A, X_gs, metrics_gs = train_v3_graphsage(df, epochs=300)
    model_rf, _, metrics_rf = train_v4_random_forest(df)
    model_lr, _, metrics_lr = train_v5_linear_regression(df)

    # ─── TASK 3: Summary Table ───
    print("\n" + "=" * 60)
    print("  TASK 3: Model Comparison Summary Table")
    print("=" * 60)

    summary = pd.DataFrame({
        'Model': ['V1: GBoost', 'V2: MLP', 'V3: GraphSAGE', 'V4: RandForest', 'V5: LinReg'],
        'MAE': [metrics_gb['MAE'], metrics_mlp['MAE'], metrics_gs['MAE'], metrics_rf['MAE'], metrics_lr['MAE']],
        'MSE': [metrics_gb['MSE'], metrics_mlp['MSE'], metrics_gs['MSE'], metrics_rf['MSE'], metrics_lr['MSE']],
        'RMSE': [metrics_gb['RMSE'], metrics_mlp['RMSE'], metrics_gs['RMSE'], metrics_rf['RMSE'], metrics_lr['RMSE']],
        'MAPE (%)': [metrics_gb['MAPE'], metrics_mlp['MAPE'], metrics_gs['MAPE'], metrics_rf['MAPE'], metrics_lr['MAPE']],
        'R²': [metrics_gb['R2'], metrics_mlp['R2'], metrics_gs['R2'], metrics_rf['R2'], metrics_lr['R2']],
    })
    print(summary.to_string(index=False))

    # ─── TASK 4: Compare Social Structures ───
    compare_social_structures()

    # ─── TASK 5: Peer Influence Analysis ───
    analyze_peer_influence(model_gb, feat_cols)

    # ─── Student Input & Prediction ───
    print("\n" + "=" * 60)
    print("  DỰ ĐOÁN ĐIỂM CỦA BẠN (5 MÔ HÌNH)")
    print("=" * 60)

    use_default = input("\n  Bạn muốn nhập điểm thủ công? (y/n, mặc định n): ").strip().lower()

    if use_default == 'y':
        academic, peers = get_student_input()
    else:
        # Default example
        academic = np.array([7.0, 8.0, 6.5, 7.5, 7.0])
        peers = np.array([7.0, 6.5, 8.0, 7.5, 7.0, 6.0, 8.5, 7.0, 7.5, 6.5])
        print(f"\n  Sử dụng điểm mặc định:")
        print(f"    Academic: {academic}")
        print(f"    Peers:    {peers}")

    predict_student_score(academic, peers, model_gb, model_mlp, model_gs, model_rf, model_lr, A, X_gs, feat_cols)

    print("\nDone! All 5 tasks completed successfully.\n")


if __name__ == '__main__':
    main()
