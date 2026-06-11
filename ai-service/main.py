"""
main.py – ai-service
====================
Unified AI service for the assignment.

Exposes:
  POST /api/chat         – GraphRAG chatbot
  POST /api/intent       – Debug intent classification
  GET  /api/kb/stats     – FAISS + Neo4j knowledge base stats
  POST /api/kb/build     – Rebuild FAISS index
  GET  /api/graph/query  – Neo4j symptom lookup
  GET  /api/recommend/   – Product recommendations
  POST /api/embed/update – Update in-memory recommendation state
  GET  /api/graph/stats  – Neo4j graph stats for recommender
  GET  /health/          – Health check
"""

from __future__ import annotations

import logging
import os
import threading
from typing import Dict, List, Optional

import numpy as np
import requests
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from graph_rag import rag_engine
from graph_rag.rag_engine import (
    NEO4J_AVAILABLE,
    _faiss_chunks,
    _faiss_index,
    build_faiss_index,
    faiss_search,
    graphrag_chat,
    load_faiss_index,
    neo4j_query_symptom,
)
from services.ai_logic import (
    INTENT_LABELS_VI,
    classify_medical_intent,
)
from services.recommender_logic import HybridRecommender, SPDManifold, get_recommender
from kb.kb_loader import load_kb_chunks, load_kb_metadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Health-AI Service",
    description="Unified AI service with GraphRAG chatbot, Neo4j knowledge graph, and GNN/SPD recommendations.",
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

PHARMACY_SERVICE_URL = os.getenv("PHARMACY_SERVICE_URL", "http://pharmacy-service:8000")

MEDICAL_KNOWLEDGE_BASE = [
    "Viêm loét dạ dày tá tràng là tình trạng niêm mạc dạ dày hoặc tá tràng bị tổn thương, hình thành vết loét.",
    "PPI là nhóm thuốc hiệu quả để điều trị các bệnh lý liên quan đến acid dạ dày.",
    "Trào ngược dạ dày thực quản xảy ra khi acid dạ dày trào ngược lên thực quản.",
    "Hội chứng ruột kích thích là rối loạn chức năng đại tràng mãn tính, không có tổn thương thực thể.",
    "Helicobacter pylori là vi khuẩn Gram âm sống trong môi trường acid của dạ dày.",
]


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=1000)
    customer_id: Optional[int] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    intent: str
    intent_label: str
    sources_count: int
    mode: str


class IntentRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)


class InteractionPayload(BaseModel):
    user_id: str
    product_id: int
    action: str
    weight: float = Field(1.0, ge=0.0, le=10.0)


class RecommendationItem(BaseModel):
    product_id: int
    score: float
    gnn_score: float
    airm_score: float
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None


class RecommendResponse(BaseModel):
    user_id: str
    top_k: int
    recommendations: List[RecommendationItem]
    method: str = "GNN + SPD-AIRM"


_kb_initialized = False
_kb_lock = threading.Lock()
_user_interactions: Dict[str, List[Dict]] = {}
_product_interactions: Dict[int, List[Dict]] = {}
_runtime_kb_chunks_count = 0


def _init_knowledge_base() -> None:
    global _kb_initialized
    global _runtime_kb_chunks_count
    with _kb_lock:
        if _kb_initialized:
            return
        try:
            kb_chunks = load_kb_chunks()
            if not kb_chunks:
                kb_chunks = MEDICAL_KNOWLEDGE_BASE
            if not load_faiss_index():
                build_faiss_index(kb_chunks)
            _runtime_kb_chunks_count = len(kb_chunks)
            _kb_initialized = True
            logger.info("[KB] Knowledge base initialized.")
        except Exception as exc:
            logger.error(f"[KB] Initialization error: {exc}")


@app.on_event("startup")
async def on_startup() -> None:
    threading.Thread(target=_init_knowledge_base, daemon=True, name="KB-Init").start()
    logger.info("[STARTUP] Health-AI Service started.")


def _get_neo4j_products() -> List[Dict]:
    if not NEO4J_AVAILABLE:
        return []
    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(os.getenv("NEO4J_URI", "bolt://neo4j:7687"), auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "health123")))
        with driver.session() as session:
            result = session.run("MATCH (p:Product) RETURN p.id AS product_id, p.name AS name LIMIT 100")
            products = [dict(record) for record in result]
        driver.close()
        return products
    except Exception as exc:
        logger.warning(f"[Neo4j] Unable to read products: {exc}")
        return []


def _get_products_info(product_ids: List[int]) -> Dict[int, Dict]:
    result = {}
    try:
        response = requests.get(f"{PHARMACY_SERVICE_URL}/products/", timeout=5)
        if response.status_code == 200:
            for item in response.json():
                if item.get("id") in product_ids:
                    result[item["id"]] = item
    except Exception as exc:
        logger.warning(f"[ProductService] {exc}")
    return result


def _build_embeddings_and_covs(user_id: str, all_product_ids: List[int]):
    user_interactions = _user_interactions.get(user_id, [])
    user_cov = SPDManifold.encode_user_behavior(user_interactions)

    rng = np.random.default_rng(seed=abs(hash(user_id)) % 2**32)
    user_emb = rng.standard_normal(64).astype(np.float32)
    user_emb /= np.linalg.norm(user_emb) + 1e-8

    prod_embeddings: Dict[int, np.ndarray] = {}
    prod_covariances: Dict[int, np.ndarray] = {}
    for pid in all_product_ids:
        rng_p = np.random.default_rng(seed=pid % 2**32)
        emb = rng_p.standard_normal(64).astype(np.float32)
        emb /= np.linalg.norm(emb) + 1e-8
        prod_embeddings[pid] = emb
        prod_covariances[pid] = SPDManifold.encode_user_behavior(_product_interactions.get(pid, []))

    return user_emb, user_cov, prod_embeddings, prod_covariances


@app.get("/health/", tags=["Health"])
def health() -> Dict:
    return {
        "status": "UP",
        "service": "ai-service",
        "kb_initialized": _kb_initialized,
        "faiss_chunks": len(rag_engine._faiss_chunks),
        "faiss_index": "ready" if rag_engine._faiss_index is not None else "not_built",
        "neo4j": "available" if NEO4J_AVAILABLE else "unavailable",
    }


@app.post("/api/chat", response_model=ChatResponse, tags=["AI Chat"])
def chat(req: ChatRequest):
    query = req.message.strip()
    if not query:
        raise HTTPException(400, "Tin nhắn không được trống")

    try:
        result = graphrag_chat(query=query, customer_id=req.customer_id)
        intent = result.get("intent", "general")
        return ChatResponse(
            answer=result["answer"],
            intent=intent,
            intent_label=INTENT_LABELS_VI.get(intent, "Câu hỏi tổng quát"),
            sources_count=result.get("sources_count", 0),
            mode=result.get("mode", "template"),
        )
    except Exception as exc:
        logger.error(f"[Chat] {exc}")
        raise HTTPException(500, f"Lỗi xử lý câu hỏi: {exc}")


@app.post("/api/intent", tags=["AI Chat"])
def detect_intent(req: IntentRequest) -> Dict:
    intent = classify_medical_intent(req.query)
    return {"query": req.query, "intent": intent, "intent_label": INTENT_LABELS_VI.get(intent, "Không xác định")}


@app.get("/api/kb/stats", tags=["Knowledge Base"])
def kb_stats() -> Dict:
    metadata = load_kb_metadata()
    return {
        "faiss_chunks": len(rag_engine._faiss_chunks),
        "faiss_index": "ready" if rag_engine._faiss_index is not None else "not_built",
        "neo4j": "available" if NEO4J_AVAILABLE else "unavailable",
        "kb_initialized": _kb_initialized,
        "runtime_chunks": _runtime_kb_chunks_count,
        "kb_file_available": metadata.get("available", False),
        "kb_products_total": metadata.get("products_total", 0),
        "kb_generated_at": metadata.get("generated_at"),
    }


@app.post("/api/kb/build", tags=["Knowledge Base"])
def build_kb(background_tasks: BackgroundTasks) -> Dict:
    def _rebuild():
        global _runtime_kb_chunks_count
        kb_chunks = load_kb_chunks()
        if not kb_chunks:
            kb_chunks = MEDICAL_KNOWLEDGE_BASE
        build_faiss_index(kb_chunks)
        _runtime_kb_chunks_count = len(kb_chunks)
        logger.info("[KB] Rebuild completed.")

    background_tasks.add_task(_rebuild)
    return {"status": "triggered", "message": "KB rebuild đang chạy nền."}


@app.get("/api/kb/sources", tags=["Knowledge Base"])
def kb_sources() -> Dict:
    return load_kb_metadata()


@app.get("/api/graph/query", tags=["Graph"])
def graph_query(symptom: str = "đau dạ dày") -> Dict:
    results = neo4j_query_symptom([symptom])
    return {"symptom": symptom, "graph_results": results, "count": len(results)}


@app.get("/api/recommend/", response_model=RecommendResponse, tags=["Recommend"])
def recommend(
    user_id: str = Query(..., description="ID người dùng"),
    top_k: int = Query(5, ge=1, le=20, description="Số sản phẩm gợi ý"),
    exclude: Optional[str] = Query(None, description="Danh sách ID đã mua, cách nhau bởi dấu phẩy"),
):
    exclude_ids: List[int] = []
    if exclude:
        try:
            exclude_ids = [int(x) for x in exclude.split(",") if x.strip()]
        except ValueError:
            raise HTTPException(400, "exclude phải là danh sách số nguyên: '1,2,3'")

    try:
        response = requests.get(f"{PHARMACY_SERVICE_URL}/products/", timeout=5)
        all_products = response.json() if response.status_code == 200 else []
    except Exception:
        all_products = []

    if not all_products:
        neo4j_products = _get_neo4j_products()
        all_product_ids = [int(item.get("product_id", idx)) for idx, item in enumerate(neo4j_products)]
        product_info: Dict[int, Dict] = {}
    else:
        all_product_ids = [item["id"] for item in all_products]
        product_info = {item["id"]: item for item in all_products}

    if not all_product_ids:
        return RecommendResponse(user_id=user_id, top_k=top_k, recommendations=[])

    user_emb, user_cov, prod_embs, prod_covs = _build_embeddings_and_covs(user_id, all_product_ids)
    recommender: HybridRecommender = get_recommender()
    raw_scores = recommender.recommend(
        user_embedding=user_emb,
        user_covariance=user_cov,
        product_embeddings=prod_embs,
        product_covariances=prod_covs,
        top_k=top_k,
        exclude_product_ids=exclude_ids,
    )

    recommendations: List[RecommendationItem] = []
    for item in raw_scores:
        pid = item["product_id"]
        info = product_info.get(pid, {})
        recommendations.append(
            RecommendationItem(
                product_id=pid,
                score=item["score"],
                gnn_score=item["gnn_score"],
                airm_score=item["airm_score"],
                name=info.get("name"),
                category=info.get("category"),
                price=float(info.get("price", 0)) if info.get("price") else None,
            )
        )

    return RecommendResponse(user_id=user_id, top_k=top_k, recommendations=recommendations)


@app.post("/api/embed/update", tags=["Recommend"])
def update_interaction(payload: InteractionPayload) -> Dict:
    _user_interactions.setdefault(payload.user_id, []).append(
        {"type": payload.action, "weight": payload.weight, "product_id": payload.product_id}
    )
    _product_interactions.setdefault(payload.product_id, []).append(
        {"type": payload.action, "weight": payload.weight}
    )
    return {"status": "ok", "message": "interaction updated"}


@app.get("/api/graph/stats", tags=["Recommend"])
def graph_stats() -> Dict:
    return {
        "neo4j": "available" if NEO4J_AVAILABLE else "unavailable",
        "users_in_memory": len(_user_interactions),
        "products_in_memory": len(_product_interactions),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
