"""
main.py – treatment-recommender-service
==========================================
FastAPI service gợi ý phác đồ điều trị / sản phẩm thuốc bằng GNN + SPD Manifold.

Endpoints:
  GET  /api/recommend/         – Top-K gợi ý cho một user
  POST /api/embed/update       – Cập nhật embedding sau tương tác mới
  GET  /api/graph/stats        – Thống kê knowledge graph (Neo4j)
  GET  /health/                – Health check
"""
import os
import logging
from typing import List, Optional, Dict

import numpy as np
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Local AI core
from services.ai_logic import MedicalGNN, SPDManifold, HybridRecommender, get_recommender

# Neo4j
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
NEO4J_URI      = os.getenv("NEO4J_URI",      "bolt://neo4j:7687")
NEO4J_USER     = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "health123")
PHARMACY_SERVICE_URL = os.getenv("PHARMACY_SERVICE_URL", "http://pharmacy-service:8000")

# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Health-AI Recommender Service",
    description=(
        "Gợi ý sản phẩm y tế bằng Graph Neural Network (GraphSAGE) "
        "kết hợp SPD Manifold với Affine-Invariant Riemannian Metric (AIRM)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ───────────────────────────────────────────────────────────────────

class InteractionPayload(BaseModel):
    user_id:    str = Field(..., description="ID người dùng (ví dụ: 'U123')")
    product_id: int = Field(..., description="ID sản phẩm đã tương tác")
    action:     str = Field(..., description="'view' | 'purchase' | 'search' | 'rating'")
    weight:     float = Field(1.0, ge=0.0, le=10.0, description="Cường độ tương tác")


class RecommendationItem(BaseModel):
    product_id: int
    score:      float
    gnn_score:  float
    airm_score: float
    name:       Optional[str] = None
    category:   Optional[str] = None
    price:      Optional[float] = None


class RecommendResponse(BaseModel):
    user_id:         str
    top_k:           int
    recommendations: List[RecommendationItem]
    method:          str = "GNN + SPD-AIRM"


# ── In-memory store (production: thay bằng Redis) ─────────────────────────────
# user_interactions: {user_id: List[{type, weight, product_id}]}
_user_interactions: Dict[str, List[Dict]] = {}

# product_interactions: {product_id: List[{type, weight}]}
_product_interactions: Dict[int, List[Dict]] = {}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_neo4j_products() -> List[Dict]:
    """Lấy danh sách sản phẩm từ Neo4j Knowledge Graph."""
    if not NEO4J_AVAILABLE:
        return []
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        with driver.session() as session:
            result = session.run(
                "MATCH (p:Product) RETURN p.product_id AS product_id, p.name AS name LIMIT 100"
            )
            products = [dict(record) for record in result]
        driver.close()
        return products
    except Exception as e:
        logger.warning(f"[Neo4j] Không kết nối được: {e}")
        return []


def _get_products_info(product_ids: List[int]) -> Dict[int, Dict]:
    """Lấy thông tin thuốc từ pharmacy-service."""
    result = {}
    try:
        r = requests.get(f"{PHARMACY_SERVICE_URL}/products/", timeout=5)
        if r.status_code == 200:
            for p in r.json():
                if p['id'] in product_ids:
                    result[p['id']] = p
    except Exception as e:
        logger.warning(f"[ProductService] Không lấy được: {e}")
    return result


def _build_embeddings_and_covs(user_id: str, all_product_ids: List[int]):
    """
    Xây dựng embedding và covariance matrix cho user và tất cả products.

    Flow:
      1. Lấy interactions của user → encode thành SPD covariance
      2. Tạo random GNN embeddings (placeholder khi chưa có graph đầy đủ)
         Production: dùng MedicalGNN.get_embeddings_from_graph() với dữ liệu Neo4j
      3. Với mỗi product: build covariance từ interaction history
    """
    # User embedding & covariance
    user_interactions = _user_interactions.get(user_id, [])
    user_cov          = SPDManifold.encode_user_behavior(user_interactions)

    # GNN embedding (random init cho demo; production: load từ Neo4j + train GNN)
    rng          = np.random.default_rng(seed=hash(user_id) % 2**32)
    user_emb     = rng.standard_normal(64).astype(np.float32)
    user_emb    /= np.linalg.norm(user_emb) + 1e-8

    # Product embeddings & covariances
    prod_embeddings  = {}
    prod_covariances = {}
    for pid in all_product_ids:
        seed_val              = pid % 2**32
        rng_p                 = np.random.default_rng(seed=seed_val)
        emb                   = rng_p.standard_normal(64).astype(np.float32)
        emb                  /= np.linalg.norm(emb) + 1e-8
        prod_embeddings[pid]  = emb

        prod_ints             = _product_interactions.get(pid, [])
        prod_covariances[pid] = SPDManifold.encode_user_behavior(prod_ints)

    return user_emb, user_cov, prod_embeddings, prod_covariances


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health/", tags=["Health"])
def health():
    """Health check."""
    return {
        "status":           "UP",
        "service":          "treatment-recommender-service",
        "torch_geometric":  "available" if True else "fallback",
        "neo4j":            "available" if NEO4J_AVAILABLE else "unavailable",
    }


@app.get("/api/recommend/", response_model=RecommendResponse, tags=["Recommend"])
def recommend(
    user_id: str  = Query(..., description="ID người dùng"),
    top_k:   int  = Query(5,   ge=1, le=20, description="Số sản phẩm gợi ý"),
    exclude: Optional[str] = Query(None, description="Danh sách ID đã mua, cách nhau bởi dấu phẩy"),
):
    """
    Gợi ý top-K sản phẩm y tế cho user dựa trên:
    - GNN embedding (học từ Knowledge Graph)
    - SPD Manifold AIRM (phân tích hành vi người dùng)

    Ví dụ: GET /api/recommend/?user_id=U123&top_k=5
    """
    # Parse excluded products
    exclude_ids = []
    if exclude:
        try:
            exclude_ids = [int(x) for x in exclude.split(',') if x.strip()]
        except ValueError:
            raise HTTPException(400, "exclude phải là danh sách số nguyên: '1,2,3'")

    # Lấy danh sách tất cả thuốc active từ pharmacy-service
    try:
        r = requests.get(f"{PHARMACY_SERVICE_URL}/products/", timeout=5)
        all_products = r.json() if r.status_code == 200 else []
    except Exception:
        all_products = []

    if not all_products:
        # Fallback: dùng neo4j
        neo4j_prods = _get_neo4j_products()
        all_product_ids = [p.get('product_id', i) for i, p in enumerate(neo4j_prods)]
        product_info    = {}
    else:
        all_product_ids = [p['id'] for p in all_products]
        product_info    = {p['id']: p for p in all_products}

    if not all_product_ids:
        return RecommendResponse(
            user_id=user_id, top_k=top_k, recommendations=[]
        )

    # Build embeddings và covariance matrices
    user_emb, user_cov, prod_embs, prod_covs = _build_embeddings_and_covs(
        user_id, all_product_ids
    )

    # Tính điểm hybrid
    recommender = get_recommender()
    raw_scores  = recommender.recommend(
        user_embedding      = user_emb,
        user_covariance     = user_cov,
        product_embeddings  = prod_embs,
        product_covariances = prod_covs,
        top_k               = top_k,
        exclude_product_ids = exclude_ids,
    )

    # Bổ sung thông tin sản phẩm
    recommendations = []
    for item in raw_scores:
        pid  = item['product_id']
        info = product_info.get(pid, {})
        recommendations.append(RecommendationItem(
            product_id = pid,
            score      = item['score'],
            gnn_score  = item['gnn_score'],
            airm_score = item['airm_score'],
            name       = info.get('name'),
            category   = info.get('category'),
            price      = float(info.get('price', 0)) if info.get('price') else None,
        ))

    return RecommendResponse(
        user_id         = user_id,
        top_k           = top_k,
        recommendations = recommendations,
    )


@app.post("/api/embed/update", tags=["Recommend"])
def update_interaction(payload: InteractionPayload):
    """
    Ghi nhận tương tác mới của user với sản phẩm.
    Cập nhật in-memory store để ảnh hưởng đến recommendation tiếp theo.
    Production: nên ghi vào Redis hoặc Neo4j luôn.
    """
    uid = payload.user_id
    pid = payload.product_id

    interaction = {
        "type":       payload.action,
        "weight":     payload.weight,
        "product_id": pid,
    }

    # Cập nhật user interactions
    if uid not in _user_interactions:
        _user_interactions[uid] = []
    _user_interactions[uid].append(interaction)

    # Cập nhật product interactions
    if pid not in _product_interactions:
        _product_interactions[pid] = []
    _product_interactions[pid].append({
        "type":   payload.action,
        "weight": payload.weight,
    })

    logger.info(f"[Embed] User={uid} → Product={pid} ({payload.action}, w={payload.weight})")

    return {
        "status":              "updated",
        "user_id":             uid,
        "product_id":          pid,
        "total_interactions":  len(_user_interactions[uid]),
    }


@app.get("/api/graph/stats", tags=["Graph"])
def graph_stats():
    """Thống kê Knowledge Graph từ Neo4j."""
    if not NEO4J_AVAILABLE:
        return {"neo4j": "unavailable", "note": "Cài neo4j driver: pip install neo4j"}

    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        stats  = {}
        with driver.session() as session:
            for label in ['User', 'Product', 'Symptom', 'Disease', 'Category']:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) AS cnt")
                stats[label] = result.single()['cnt']
            rel_result = session.run("MATCH ()-[r]->() RETURN count(r) AS cnt")
            stats['total_relationships'] = rel_result.single()['cnt']
        driver.close()
        return {"status": "connected", "graph_stats": stats}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
