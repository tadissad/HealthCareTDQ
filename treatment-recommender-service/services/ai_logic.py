"""
ai_logic.py – recommender-ai-service / services/
==================================================
Core AI module thực hiện 2 thuật toán chính:

1. MedicalGNN (Graph Neural Network):
   - Kiến trúc: 2 lớp GraphSAGE (SAGEConv) từ PyTorch Geometric
   - Input: Feature matrix X (N × D) + Cạnh đồ thị edge_index (2 × E)
   - Output: Embedding vector 64-dim cho mỗi node (User / Product / Symptom)
   - Mục đích: Học biểu diễn sâu từ Knowledge Graph (Neo4j)

2. SPDManifold (Symmetric Positive Definite Manifold):
   - Lý thuyết: Ma trận SPD tạo thành đa tạp Riemann. AIRM đo geodesic distance:
       d_AIRM(S₁, S₂) = ‖log(S₁^{-1/2} S₂ S₁^{-1/2})‖_F
   - Ứng dụng: Mô hóa sự không chắc chắn trong hành vi người dùng
     qua ma trận hiệp phương sai (covariance matrix) của các tương tác:
     (view_weight, purchase_weight, search_weight, rating_weight)
   - Khoảng cách AIRM nhỏ hơn ⟹ hành vi tương đồng hơn ⟹ gợi ý liên quan hơn

3. HybridRecommender:
   - Kết hợp GNN cosine similarity + AIRM similarity với trọng số α
   - Score cuối = α × GNN_score + (1-α) × AIRM_score
"""
import os
import logging
from typing import List, Dict, Optional, Tuple

import numpy as np
from scipy.linalg import logm

logger = logging.getLogger(__name__)

# ── PyTorch Geometric (optional, graceful fallback) ────────────────────────────
try:
    import torch
    import torch.nn.functional as F
    from torch_geometric.nn import SAGEConv
    from torch_geometric.data import Data
    TORCH_GEO_AVAILABLE = True
    logger.info("[GNN] PyTorch Geometric loaded successfully.")
except ImportError:
    TORCH_GEO_AVAILABLE = False
    logger.warning("[GNN] torch_geometric không tìm thấy. Dùng NumPy embedding fallback.")


# ══════════════════════════════════════════════════════════════════════════════
# 1. GRAPH NEURAL NETWORK (GNN)
# ══════════════════════════════════════════════════════════════════════════════

class MedicalGNN(torch.nn.Module if TORCH_GEO_AVAILABLE else object):
    """
    Graph Neural Network cho Medical Knowledge Graph.

    Kiến trúc: GraphSAGE với 2 lớp convolution (Inductive Learning):
      Layer 1: SAGEConv(in_channels=64, out=128) + ReLU + Dropout(0.3)
      Layer 2: SAGEConv(in=128, out=64)

    Dữ liệu đầu vào (từ Neo4j):
      - Nodes: User, Medicine (Product), Symptom, Disease, Category
      - Edges: PURCHASED, VIEWED, SEARCHED, INDICATES, TREATED_BY, BELONGS_TO

    Tham khảo: Hamilton et al., "Inductive Representation Learning on Large Graphs"
               (NeurIPS 2017) — GraphSAGE
    """

    IN_CHANNELS     = 64
    HIDDEN_CHANNELS = 128
    OUT_CHANNELS    = 64

    def __init__(self):
        if not TORCH_GEO_AVAILABLE:
            return

        super().__init__()
        self.conv1 = SAGEConv(self.IN_CHANNELS, self.HIDDEN_CHANNELS)
        self.conv2 = SAGEConv(self.HIDDEN_CHANNELS, self.OUT_CHANNELS)
        logger.info("[GNN] MedicalGNN khởi tạo: 64→128→64 (GraphSAGE)")

    def forward(self, x: 'torch.Tensor', edge_index: 'torch.Tensor') -> 'torch.Tensor':
        """
        Forward pass qua 2 lớp GraphSAGE.

        Args:
            x:          (N, 64)  – Feature matrix của N nodes
            edge_index: (2, E)   – Danh sách cạnh định hướng

        Returns:
            (N, 64) – Embedding vectors sau khi học từ cấu trúc đồ thị
        """
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=0.3, training=self.training)
        x = self.conv2(x, edge_index)
        return x

    @classmethod
    def get_embeddings_from_graph(cls, node_features: np.ndarray,
                                  edges: List[Tuple[int, int]]) -> np.ndarray:
        """
        Tính GNN embedding cho tất cả nodes.

        Args:
            node_features: (N, 64) numpy array – Đặc trưng khởi tạo của mỗi node
            edges:         List[(src, dst)]     – Danh sách cạnh từ Neo4j

        Returns:
            (N, 64) numpy array – Embedding sau khi qua GNN
        """
        if not TORCH_GEO_AVAILABLE or len(node_features) == 0:
            logger.warning("[GNN] Dùng raw features vì torch_geometric không sẵn sàng.")
            return node_features

        try:
            x = torch.tensor(node_features, dtype=torch.float)

            if edges:
                edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
            else:
                # Không có cạnh → trả về embedding nguyên bản
                return node_features

            model = cls()
            model.eval()
            with torch.no_grad():
                embeddings = model(x, edge_index)
            return embeddings.numpy()

        except Exception as e:
            logger.error(f"[GNN] Forward pass thất bại: {e}")
            return node_features


# ══════════════════════════════════════════════════════════════════════════════
# 2. SPD MANIFOLD (Affine-Invariant Riemannian Metric)
# ══════════════════════════════════════════════════════════════════════════════

class SPDManifold:
    """
    Không gian đa tạp SPD (Symmetric Positive Definite) với Affine-Invariant
    Riemannian Metric (AIRM).

    Ứng dụng trong hệ thống này:
    ─────────────────────────────
    Mỗi người dùng có một "hành vi profile" được biểu diễn bằng ma trận
    hiệp phương sai (covariance) của các tương tác theo thời gian:

        Σ_user = Cov(Behavior_Vectors)   ← D×D SPD matrix (D=4)

    Vector hành vi mỗi lần tương tác:
        b = [view_weight, purchase_weight, search_weight, rating_weight]

    Hai người dùng có hành vi tương đồng ⟺ Σ_u1 và Σ_u2 gần nhau trên đa tạp SPD.

    Công thức AIRM:
        d_AIRM(S₁, S₂) = ‖log(S₁^{-1/2} S₂ S₁^{-1/2})‖_F

    Tham khảo: Arsigny et al., "Geometric Means in a Novel Vector Space Structure
               on Symmetric Positive-Definite Matrices" (SIAM 2007)
    """

    BEHAVIOR_DIM = 4  # [view, purchase, search, rating]
    EPSILON      = 1e-5  # Regularization for SPD guarantee

    @classmethod
    def build_covariance_matrix(cls, behavior_vectors: np.ndarray) -> np.ndarray:
        """
        Xây dựng ma trận SPD từ lịch sử hành vi người dùng.

        Args:
            behavior_vectors: (N, 4) array với N = số lần tương tác,
                              4 features = [view_w, purchase_w, search_w, rating_w]

        Returns:
            (4, 4) SPD covariance matrix.
            Nếu N < 2, trả về ma trận đơn vị (không có thông tin).
        """
        if behavior_vectors is None or len(behavior_vectors) < 2:
            D = cls.BEHAVIOR_DIM
            logger.debug("[SPD] Không đủ dữ liệu, dùng identity matrix.")
            return np.eye(D) * cls.EPSILON

        cov = np.cov(behavior_vectors.T)          # (D, D)
        cov += np.eye(cov.shape[0]) * cls.EPSILON  # Regularize → đảm bảo positive definite
        return cov

    @staticmethod
    def matrix_sqrt_inv(S: np.ndarray) -> np.ndarray:
        """
        Tính S^{-1/2} qua phân tích trị riêng (eigendecomposition).

        S = V Λ V^T  →  S^{-1/2} = V Λ^{-1/2} V^T
        """
        eigenvalues, eigenvectors = np.linalg.eigh(S)
        eigenvalues = np.clip(eigenvalues, 1e-10, None)  # Tránh chia cho 0
        sqrt_inv_diag = np.diag(1.0 / np.sqrt(eigenvalues))
        return eigenvectors @ sqrt_inv_diag @ eigenvectors.T

    @classmethod
    def airm_distance(cls, S1: np.ndarray, S2: np.ndarray) -> float:
        """
        Tính khoảng cách AIRM giữa hai ma trận SPD S1 và S2.

        Công thức:
            d_AIRM(S₁, S₂) = ‖log(S₁^{-1/2} S₂ S₁^{-1/2})‖_F

        Trong đó:
          - log(·) là matrix logarithm
          - ‖·‖_F là Frobenius norm

        Args:
            S1, S2: (D, D) SPD matrices

        Returns:
            Scalar float – geodesic distance trên đa tạp SPD
        """
        try:
            S1_half_inv = cls.matrix_sqrt_inv(S1)
            M = S1_half_inv @ S2 @ S1_half_inv   # M = S₁^{-1/2} S₂ S₁^{-1/2}
            log_M = logm(M)                        # Ma trận logarithm
            distance = np.linalg.norm(log_M, 'fro')  # Frobenius norm
            return float(np.real(distance))

        except Exception as e:
            logger.warning(f"[SPD] AIRM thất bại ({e}), fallback → Frobenius norm.")
            return float(np.linalg.norm(S1 - S2, 'fro'))

    @classmethod
    def similarity(cls, distance: float, scale: float = 2.0) -> float:
        """
        Chuyển AIRM distance → similarity score trong [0, 1].

        Dùng kernel Gaussian: sim = exp(-d / scale)
        scale lớn hơn → smooth hơn, ít nhạy với khoảng cách lớn.
        """
        return float(np.exp(-distance / scale))

    @classmethod
    def encode_user_behavior(cls, interactions: List[Dict]) -> np.ndarray:
        """
        Chuyển danh sách tương tác người dùng → ma trận SPD.

        Args:
            interactions: List[{
                "type": "view"|"purchase"|"search"|"rating",
                "weight": float,  # cường độ tương tác
                "product_id": int
            }]

        Returns:
            (4, 4) SPD covariance matrix
        """
        if not interactions:
            return np.eye(cls.BEHAVIOR_DIM) * cls.EPSILON

        vectors = []
        for it in interactions:
            itype  = it.get('type', 'view')
            weight = float(it.get('weight', 1.0))

            # Mã hóa loại tương tác thành 4-dim vector
            vec = [0.0, 0.0, 0.0, 0.0]
            type_map = {'view': 0, 'purchase': 1, 'search': 2, 'rating': 3}
            idx = type_map.get(itype, 0)
            vec[idx] = weight
            vectors.append(vec)

        behavior_matrix = np.array(vectors)  # (N, 4)
        return cls.build_covariance_matrix(behavior_matrix)


# ══════════════════════════════════════════════════════════════════════════════
# 3. HYBRID RECOMMENDER
# ══════════════════════════════════════════════════════════════════════════════

class HybridRecommender:
    """
    Bộ gợi ý kết hợp GNN + SPD Manifold.

    Scoring formula:
        final_score(product_i) = α × GNN_cosine(user_emb, product_emb_i)
                               + (1-α) × AIRM_sim(user_cov, product_behavior_cov_i)

    Mặc định α = 0.6 (GNN chiếm ưu thế nhưng vẫn kết hợp SPD uncertainty modeling)
    """

    def __init__(self, alpha: float = 0.6):
        self.alpha = alpha
        logger.info(f"[Recommender] HybridRecommender khởi tạo: α={alpha}")

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Cosine similarity giữa 2 embedding vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def recommend(
        self,
        user_embedding: np.ndarray,
        user_covariance: np.ndarray,
        product_embeddings: Dict[int, np.ndarray],
        product_covariances: Dict[int, np.ndarray],
        top_k: int = 5,
        exclude_product_ids: Optional[List[int]] = None,
    ) -> List[Dict]:
        """
        Tính top-K sản phẩm gợi ý cho user.

        Args:
            user_embedding:      (64,) GNN embedding của user
            user_covariance:     (4,4) SPD covariance của hành vi user
            product_embeddings:  {product_id: (64,) embedding}
            product_covariances: {product_id: (4,4) SPD covariance}
            top_k:               Số sản phẩm trả về
            exclude_product_ids: Loại trừ sản phẩm đã mua

        Returns:
            List[{"product_id": int, "score": float, "gnn_score": float, "airm_score": float}]
        """
        exclude = set(exclude_product_ids or [])
        scores  = []

        for product_id, prod_emb in product_embeddings.items():
            if product_id in exclude:
                continue

            # GNN similarity (cosine)
            gnn_score = (self._cosine_similarity(user_embedding, prod_emb) + 1) / 2  # normalize to [0,1]

            # SPD similarity (AIRM)
            prod_cov = product_covariances.get(product_id, np.eye(SPDManifold.BEHAVIOR_DIM) * SPDManifold.EPSILON)
            airm_dist = SPDManifold.airm_distance(user_covariance, prod_cov)
            airm_score = SPDManifold.similarity(airm_dist)

            # Hybrid final score
            final_score = self.alpha * gnn_score + (1 - self.alpha) * airm_score

            scores.append({
                "product_id": product_id,
                "score":      round(final_score, 4),
                "gnn_score":  round(gnn_score,   4),
                "airm_score": round(airm_score,  4),
            })

        scores.sort(key=lambda x: x['score'], reverse=True)
        return scores[:top_k]


# ── Singleton instances ────────────────────────────────────────────────────────
_recommender = HybridRecommender(alpha=0.6)


def get_recommender() -> HybridRecommender:
    """Trả về singleton HybridRecommender."""
    return _recommender
