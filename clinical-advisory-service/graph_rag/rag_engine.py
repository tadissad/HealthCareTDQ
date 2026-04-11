"""
rag_engine.py – ai-consulting-service / graph_rag/
====================================================
GraphRAG Pipeline: kết hợp 3 nguồn tri thức:

  1. Neo4j Knowledge Graph – Quan hệ có cấu trúc:
       (Symptom)-[:INDICATES]->(Disease)-[:TREATED_BY]->(Product)
       (User)-[:SEARCHED {weight}]->(Symptom)

  2. FAISS Vector Store – Tài liệu y khoa phi cấu trúc:
       Encoding bằng Gemini text-embedding-004 API (768-dim, tiếng Việt tốt)
       Tìm kiếm top-K chunks tương đồng ngữ nghĩa với câu hỏi

  3. product-service – Thông tin sản phẩm thực tế:
       Fetch qua REST API, filter theo symptom_tags

Flow đầy đủ:
  query → intent → [Neo4j + FAISS + product-service] → context → Gemini 1.5 Flash → answer + disclaimer
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import numpy as np
import requests

logger = logging.getLogger(__name__)

# ── Config từ biến môi trường ─────────────────────────────────────────────────
NEO4J_URI           = os.getenv("NEO4J_URI",           "bolt://neo4j:7687")
NEO4J_USER          = os.getenv("NEO4J_USER",          "neo4j")
NEO4J_PASSWORD      = os.getenv("NEO4J_PASSWORD",      "health123")
GEMINI_API_KEY      = os.getenv("GEMINI_API_KEY",      "")
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8000")
FAISS_INDEX_PATH    = os.getenv("FAISS_INDEX_PATH",    "/app/faiss_data")
EMBEDDING_MODEL     = os.getenv("EMBEDDING_MODEL",     "paraphrase-multilingual-MiniLM-L12-v2")

# ── Optional imports (graceful fallback) ──────────────────────────────────────
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("[FAISS] faiss-cpu không tìm thấy. Vector search sẽ bị bỏ qua.")

# NOTE: Không dùng SentenceTransformer local nữa.
# Dùng Gemini text-embedding-004 API – nhẹ hơn ~1.2GB, chất lượng tốt hơn.
EMBEDDING_AVAILABLE = False  # Sẽ set True sau khi verify Gemini key

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

try:
    import google.generativeai as genai
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
        EMBEDDING_AVAILABLE = True  # Gemini embed có thể dùng
        logger.info("[Gemini] API configured. Dùng text-embedding-004 cho FAISS.")
    else:
        GEMINI_AVAILABLE = False
        logger.warning("[Gemini] Chưa có API key – FAISS embedding bị tắt.")
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("[Gemini] google-generativeai không tìm thấy. Dùng template fallback.")


# ══════════════════════════════════════════════════════════════════════════════
# FAISS VECTOR STORE
# ══════════════════════════════════════════════════════════════════════════════

_faiss_index:  Optional[object] = None  # faiss.IndexFlatIP
_faiss_chunks: List[str] = []           # Danh sách text chunks tương ứng với từng vector


def _get_embedding(text: str) -> Optional[np.ndarray]:
    """
    Encode text thành vector 768-dim bằng Gemini text-embedding-004.
    Không cần tải model về máy – gọi API trực tiếp.
    Tốt hơn MiniLM: hiểu ngữ cảnh tiếng Việt, y khoa chuyên sâu.
    """
    if not EMBEDDING_AVAILABLE or not GEMINI_API_KEY:
        return None
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="RETRIEVAL_DOCUMENT",
        )
        emb = np.array(result["embedding"], dtype=np.float32)
        # Normalize để dùng với IndexFlatIP (cosine similarity)
        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm
        return emb
    except Exception as e:
        logger.error(f"[Embed] Gemini embedding lỗi: {e}")
        return None


def _get_query_embedding(text: str) -> Optional[np.ndarray]:
    """Encode câu hỏi (query) với task_type RETRIEVAL_QUERY."""
    if not EMBEDDING_AVAILABLE or not GEMINI_API_KEY:
        return None
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="RETRIEVAL_QUERY",
        )
        emb = np.array(result["embedding"], dtype=np.float32)
        norm = np.linalg.norm(emb)
        if norm > 0:
            emb = emb / norm
        return emb
    except Exception as e:
        logger.error(f"[Embed] Gemini query embedding lỗi: {e}")
        return None


def build_faiss_index(chunks: List[str]) -> bool:
    """
    Xây dựng FAISS index từ danh sách text chunks.
    Dùng IndexFlatIP (Inner Product) với normalized vectors → tương đương cosine similarity.

    Args:
        chunks: List[str] – Các đoạn văn bản y khoa

    Returns:
        True nếu thành công, False nếu lỗi
    """
    global _faiss_index, _faiss_chunks

    if not FAISS_AVAILABLE or not EMBEDDING_AVAILABLE:
        logger.warning("[FAISS] Bỏ qua build_faiss_index do thiếu thư viện.")
        _faiss_chunks = chunks  # Vẫn lưu chunks để dùng fallback
        return False

    try:
        embeddings = []
        valid_chunks = []
        for chunk in chunks:
            emb = _get_embedding(chunk)
            if emb is not None:
                embeddings.append(emb)
                valid_chunks.append(chunk)

        if not embeddings:
            return False

        dim   = len(embeddings[0])
        index = faiss.IndexFlatIP(dim)           # Inner Product (cosine với normalized vectors)
        matrix = np.vstack(embeddings).astype(np.float32)
        index.add(matrix)

        _faiss_index  = index
        _faiss_chunks = valid_chunks

        # Lưu xuống disk
        faiss_path = Path(FAISS_INDEX_PATH)
        faiss_path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(faiss_path / "medical.index"))
        with open(str(faiss_path / "chunks.json"), "w", encoding="utf-8") as f:
            json.dump(valid_chunks, f, ensure_ascii=False, indent=2)

        logger.info(f"[FAISS] Index xây dựng thành công: {len(valid_chunks)} chunks, dim={dim}")
        return True

    except Exception as e:
        logger.error(f"[FAISS] Lỗi build index: {e}")
        return False


def load_faiss_index() -> bool:
    """Nạp FAISS index từ disk (dùng khi service restart)."""
    global _faiss_index, _faiss_chunks

    if not FAISS_AVAILABLE:
        return False

    faiss_path = Path(FAISS_INDEX_PATH)
    index_file = faiss_path / "medical.index"
    chunks_file = faiss_path / "chunks.json"

    if not index_file.exists() or not chunks_file.exists():
        logger.info("[FAISS] Không tìm thấy index đã lưu.")
        return False

    try:
        _faiss_index = faiss.read_index(str(index_file))
        with open(str(chunks_file), "r", encoding="utf-8") as f:
            _faiss_chunks = json.load(f)
        logger.info(f"[FAISS] Index nạp thành công: {len(_faiss_chunks)} chunks")
        return True
    except Exception as e:
        logger.error(f"[FAISS] Không nạp được index: {e}")
        return False


def faiss_search(query: str, top_k: int = 3) -> List[str]:
    """
    Tìm kiếm ngữ nghĩa top-K chunks liên quan nhất tới câu hỏi.

    Args:
        query: Câu hỏi của người dùng
        top_k: Số chunks trả về

    Returns:
        List[str] – Các đoạn văn bản y khoa liên quan nhất
    """
    if not _faiss_chunks:
        return []

    if not FAISS_AVAILABLE or _faiss_index is None:
        # Fallback: trả về chunks đầu tiên mà không có semantic search
        logger.warning("[FAISS] Fallback: trả về chunks không filter.")
        return _faiss_chunks[:top_k]

    query_emb = _get_query_embedding(query)
    if query_emb is None:
        return _faiss_chunks[:top_k]

    try:
        query_matrix = query_emb.reshape(1, -1)
        distances, indices = _faiss_index.search(query_matrix, top_k)
        results = []
        for idx in indices[0]:
            if 0 <= idx < len(_faiss_chunks):
                results.append(_faiss_chunks[idx])
        return results
    except Exception as e:
        logger.error(f"[FAISS] Lỗi search: {e}")
        return _faiss_chunks[:top_k]


# ══════════════════════════════════════════════════════════════════════════════
# NEO4J GRAPH RETRIEVAL
# ══════════════════════════════════════════════════════════════════════════════

def neo4j_query_symptom(symptom_keywords: List[str]) -> List[Dict]:
    """
    Truy vấn Knowledge Graph tìm:
      (Symptom)-[:INDICATES]->(Disease)-[:TREATED_BY]->(Product)

    Args:
        symptom_keywords: List từ khóa triệu chứng

    Returns:
        List[{symptom, disease, product, category}]
    """
    if not NEO4J_AVAILABLE or not symptom_keywords:
        return []

    results = []
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        with driver.session() as session:
            for keyword in symptom_keywords[:3]:  # Giới hạn 3 từ khóa
                cypher = """
                MATCH (s:Symptom)-[:INDICATES]->(d:Disease)-[:TREATED_BY]->(p:Product)
                WHERE toLower(s.name) CONTAINS toLower($keyword)
                OPTIONAL MATCH (p)-[:BELONGS_TO]->(c:Category)
                RETURN s.name AS symptom, d.name AS disease,
                       p.name AS product, c.name AS category
                LIMIT 5
                """
                result = session.run(cypher, keyword=keyword)
                for record in result:
                    results.append(dict(record))
        driver.close()
    except Exception as e:
        logger.warning(f"[Neo4j] Lỗi query: {e}")

    return results


def neo4j_query_product(product_name: str) -> List[Dict]:
    """Tìm thông tin sản phẩm trực tiếp từ Knowledge Graph."""
    if not NEO4J_AVAILABLE:
        return []

    results = []
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        with driver.session() as session:
            cypher = """
            MATCH (p:Product)
            WHERE toLower(p.name) CONTAINS toLower($name)
            OPTIONAL MATCH (p)-[:BELONGS_TO]->(c:Category)
            OPTIONAL MATCH (d:Disease)-[:TREATED_BY]->(p)
            RETURN p.name AS product, c.name AS category, collect(d.name) AS diseases
            LIMIT 3
            """
            result = session.run(cypher, name=product_name)
            for record in result:
                results.append(dict(record))
        driver.close()
    except Exception as e:
        logger.warning(f"[Neo4j] product query lỗi: {e}")

    return results


# ══════════════════════════════════════════════════════════════════════════════
# PRODUCT SERVICE INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════

def fetch_products_by_symptom(symptom: str, limit: int = 5) -> List[Dict]:
    """Lấy sản phẩm từ product-service filter theo symptom_tags."""
    try:
        r = requests.get(
            f"{PRODUCT_SERVICE_URL}/products/",
            params={"symptom": symptom},
            timeout=5,
        )
        if r.status_code == 200:
            return r.json()[:limit]
    except Exception as e:
        logger.warning(f"[ProductService] Lỗi fetch: {e}")
    return []


def fetch_all_products(limit: int = 10) -> List[Dict]:
    """Lấy tất cả sản phẩm active từ product-service."""
    try:
        r = requests.get(f"{PRODUCT_SERVICE_URL}/products/", timeout=5)
        if r.status_code == 200:
            return r.json()[:limit]
    except Exception as e:
        logger.warning(f"[ProductService] Lỗi: {e}")
    return []


# ══════════════════════════════════════════════════════════════════════════════
# LLM GENERATION (GEMINI 1.5 FLASH)
# ══════════════════════════════════════════════════════════════════════════════

def generate_with_gemini(prompt: str) -> Optional[str]:
    """
    Gọi Gemini 1.5 Flash API để sinh câu trả lời.

    Args:
        prompt: Prompt đã được xây dựng đầy đủ context

    Returns:
        Câu trả lời từ Gemini, hoặc None nếu lỗi
    """
    if not GEMINI_AVAILABLE or not GEMINI_API_KEY:
        logger.warning("[Gemini] API key chưa cấu hình. Dùng template fallback.")
        return None

    try:
        model  = genai.GenerativeModel("gemini-1.5-flash")
        result = model.generate_content(prompt)
        return result.text
    except Exception as e:
        logger.error(f"[Gemini] Lỗi generate: {e}")
        return None


def _template_response(query: str, products: List[Dict], intent: str) -> str:
    """Fallback khi không có Gemini API key – trả về response cấu trúc sẵn."""
    response_parts = [f"**Đây là thông tin tôi tìm được về câu hỏi của bạn:** *'{query}'*\n"]

    if products:
        response_parts.append("**Sản phẩm y tế phù hợp:**")
        for p in products[:3]:
            name  = p.get('name', 'N/A')
            price = p.get('price', 'N/A')
            desc  = p.get('description', '')[:100]
            response_parts.append(f"• **{name}** – {float(price):,.0f} VND\n  {desc}...")
    else:
        response_parts.append(
            "Hiện tại hệ thống không tìm thấy sản phẩm trực tiếp phù hợp. "
            "Vui lòng tham khảo thêm danh mục thuốc hoặc liên hệ dược sĩ."
        )

    return "\n\n".join(response_parts)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN GraphRAG PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def graphrag_chat(
    query: str,
    customer_id: Optional[int] = None,
) -> Dict:
    """
    Pipeline GraphRAG đầy đủ:

    1. Phân loại intent
    2. Trích xuất từ khóa triệu chứng
    3. Truy vấn Neo4j (structured knowledge)
    4. Fetch sản phẩm từ product-service (realtime inventory)
    5. FAISS semantic search (unstructured documents)
    6. Build prompt cho LLM
    7. Generate với Gemini 1.5 Flash
    8. Inject medical disclaimer

    Args:
        query:       Câu hỏi của người dùng
        customer_id: ID khách hàng (optional, để cá nhân hóa)

    Returns:
        {
            "answer":        str   – Câu trả lời + disclaimer
            "intent":        str   – Intent được phân loại
            "sources_count": int   – Số lượng nguồn sử dụng
            "mode":          str   – "gemini" hoặc "template"
        }
    """
    from services.ai_logic import (
        classify_medical_intent, inject_medical_disclaimer,
        format_graph_context, format_product_context,
        format_faiss_context, build_llm_prompt,
    )

    # ── Bước 1: Classify intent ───────────────────────────────────────────────
    intent = classify_medical_intent(query)
    logger.info(f"[RAG] Query='{query[:60]}' Intent={intent}")

    # ── Bước 2: Trích xuất từ khóa đơn giản (production: dùng NER) ───────────
    SYMPTOM_KEYWORDS = [
        "đau dạ dày", "ợ chua", "đầy bụng", "tiêu chảy", "táo bón",
        "buồn nôn", "nôn", "trào ngược", "viêm loét", "helicobacter",
        "đau bụng", "chướng bụng", "khó tiêu",
    ]
    query_lower = query.lower()
    matched_keywords = [kw for kw in SYMPTOM_KEYWORDS if kw in query_lower]
    if not matched_keywords:
        matched_keywords = ["dạ dày"]  # Fallback key

    sources_count = 0

    # ── Bước 3: Neo4j query ───────────────────────────────────────────────────
    graph_results = neo4j_query_symptom(matched_keywords)
    graph_context = format_graph_context(graph_results)
    if graph_results:
        sources_count += len(graph_results)

    # ── Bước 4: Product-service ───────────────────────────────────────────────
    products = []
    for kw in matched_keywords[:2]:
        products.extend(fetch_products_by_symptom(kw))
    if not products:
        products = fetch_all_products(5)
    product_context = format_product_context(products)
    if products:
        sources_count += len(products)

    # ── Bước 5: FAISS semantic search ─────────────────────────────────────────
    faiss_chunks = faiss_search(query, top_k=3)
    faiss_context = format_faiss_context(faiss_chunks)
    if faiss_chunks:
        sources_count += len(faiss_chunks)

    # ── Bước 6: Build prompt ──────────────────────────────────────────────────
    prompt = build_llm_prompt(
        user_query      = query,
        graph_context   = graph_context,
        product_context = product_context,
        faiss_context   = faiss_context,
        intent          = intent,
    )

    # ── Bước 7: Generate ──────────────────────────────────────────────────────
    gemini_answer = generate_with_gemini(prompt)
    mode = "gemini" if gemini_answer else "template"
    raw_answer = gemini_answer or _template_response(query, products, intent)

    # ── Bước 8: Inject disclaimer ─────────────────────────────────────────────
    final_answer = inject_medical_disclaimer(raw_answer, intent)

    return {
        "answer":        final_answer,
        "intent":        intent,
        "sources_count": sources_count,
        "mode":          mode,
    }
