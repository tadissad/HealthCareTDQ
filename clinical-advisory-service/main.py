"""
main.py – ai-consulting-service
================================
FastAPI chatbot tư vấn y tế với GraphRAG (Neo4j + FAISS + Gemini 1.5 Flash).

Endpoints:
  POST /api/chat            – GraphRAG chatbot chính
  POST /api/intent          – Debug: phân loại intent câu hỏi
  GET  /api/kb/stats        – Thống kê knowledge base (FAISS + Neo4j)
  POST /api/kb/build        – Rebuild FAISS index từ medical documents
  GET  /api/graph/query     – Debug: query Neo4j trực tiếp
  GET  /health/             – Health check
"""
import os
import threading
import logging
from typing import Optional, List

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Health-AI Consulting Service",
    description=(
        "Chatbot tư vấn y tế thông minh sử dụng GraphRAG:\n"
        "- Neo4j Knowledge Graph (triệu chứng-bệnh-thuốc)\n"
        "- FAISS Vector Store (tài liệu y khoa)\n"
        "- Gemini 1.5 Flash (LLM tổng hợp câu trả lời)\n"
        "- Medical Disclaimer tự động"
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

class ChatRequest(BaseModel):
    message:     str          = Field(..., min_length=2, max_length=1000, description="Câu hỏi tư vấn y tế")
    customer_id: Optional[int]= Field(None, description="ID khách hàng (cá nhân hóa)")
    session_id:  Optional[str]= Field(None, description="Session ID")


class ChatResponse(BaseModel):
    answer:        str
    intent:        str
    intent_label:  str
    sources_count: int
    mode:          str


class IntentRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)


# ── FAISS Medical Knowledge Base (seed khi startup) ───────────────────────────
MEDICAL_KNOWLEDGE_BASE = [
    """Viêm loét dạ dày tá tràng (Peptic Ulcer Disease) là tình trạng niêm mạc dạ dày 
    hoặc tá tràng bị tổn thương, hình thành vết loét. Nguyên nhân phổ biến nhất là 
    vi khuẩn Helicobacter pylori (H. pylori) và việc sử dụng thuốc kháng viêm không 
    steroid (NSAIDs). Triệu chứng điển hình: đau bụng thượng vị, đau tăng khi đói,
    buồn nôn, ợ chua. Điều trị: kết hợp kháng sinh diệt H.pylori (Amoxicillin, 
    Clarithromycin, Metronidazole) và thuốc ức chế bơm proton PPI (Omeprazole, Esomeprazole).""",

    """Thuốc ức chế bơm proton (PPI - Proton Pump Inhibitors) là nhóm thuốc hiệu quả 
    nhất để điều trị các bệnh lý liên quan đến acid dạ dày. Cơ chế: ức chế enzyme 
    H+/K+-ATPase trên tế bào thành dạ dày, làm giảm tiết acid lên đến 90%. 
    Các PPI phổ biến: Omeprazole 20mg, Esomeprazole (Nexium) 20-40mg, Pantoprazole 40mg, 
    Lansoprazole 30mg. Tác dụng phụ thường gặp: đau đầu, tiêu chảy, buồn nôn. 
    Lưu ý: không dùng dài hạn vì nguy cơ loãng xương và thiếu vitamin B12.""",

    """Trào ngược dạ dày thực quản (GERD - Gastroesophageal Reflux Disease) xảy ra khi 
    acid dạ dày trào ngược lên thực quản do cơ vòng thực quản dưới yếu hoặc giãn bất thường.
    Triệu chứng: ợ chua, ợ nóng (heartburn), đau ngực, khó nuốt, ho mãn tính. 
    Điều trị: thay đổi lối sống (giảm cân, không ăn trước khi ngủ 3 tiếng, tránh thức ăn 
    gây kích thích), dùng thuốc kháng acid (Phosphalugel, Maalox), PPI, hoặc thuốc 
    ức chế H2 (Ranitidine, Famotidine).""",

    """Hội chứng ruột kích thích (IBS - Irritable Bowel Syndrome) là rối loạn chức năng 
    đại tràng mãn tính, không có tổn thương thực thể. Triệu chứng: đau bụng, chướng bụng,
    tiêu chảy và/hoặc táo bón xen kẽ. Phân loại: IBS-D (tiêu chảy), IBS-C (táo bón), 
    IBS-M (hỗn hợp). Điều trị: thay đổi chế độ ăn (FODMAP thấp), probiotics 
    (Lactobacillus, Bifidobacterium), thuốc chống co thắt (Duspatalin/Mebeverine), 
    thuốc điều hòa nhu động ruột. Stress là yếu tố kích hoạt quan trọng.""",

    """Helicobacter pylori (H. pylori) là vi khuẩn Gram âm sống trong môi trường acid 
    của dạ dày. Đây là nguyên nhân hàng đầu gây viêm dạ dày mãn tính, loét dạ dày, 
    và là yếu tố nguy cơ ung thư dạ dày. Chẩn đoán: test hơi thở (urea breath test), 
    xét nghiệm kháng nguyên phân, hoặc sinh thiết nội soi. Phác đồ điều trị tiêu chuẩn 
    (Triple therapy 14 ngày): PPI + Amoxicillin 1g × 2/ngày + Clarithromycin 500mg × 2/ngày.
    Phác đồ thứ hai (nếu thất bại): Bismuth quadruple therapy.""",
]

_kb_initialized = False
_kb_lock = threading.Lock()


def _init_knowledge_base():
    """Khởi tạo FAISS index khi service start."""
    global _kb_initialized
    with _kb_lock:
        if not _kb_initialized:
            try:
                from graph_rag.rag_engine import build_faiss_index, load_faiss_index
                # Thử load từ disk trước
                if not load_faiss_index():
                    # Build mới từ knowledge base
                    build_faiss_index(MEDICAL_KNOWLEDGE_BASE)
                _kb_initialized = True
                logger.info("[KB] Knowledge base khởi tạo thành công.")
            except Exception as e:
                logger.error(f"[KB] Lỗi khởi tạo: {e}")


@app.on_event("startup")
async def on_startup():
    """Non-blocking: khởi tạo KB trong background thread."""
    t = threading.Thread(target=_init_knowledge_base, daemon=True, name="KB-Init")
    t.start()
    logger.info("[STARTUP] AI Consulting Service v1.0.0 started.")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health/", tags=["Health"])
def health():
    """Health check."""
    return {
        "status":         "UP",
        "service":        "ai-consulting-service",
        "kb_initialized": _kb_initialized,
        "version":        "1.0.0",
    }


@app.post("/api/chat", response_model=ChatResponse, tags=["AI Chat"])
def chat(req: ChatRequest):
    """
    GraphRAG Chatbot tư vấn y tế.

    Pipeline:
      intent → Neo4j query → product-service → FAISS search → Gemini → disclaimer
    """
    query = req.message.strip()
    if not query:
        raise HTTPException(400, "Tin nhắn không được trống")

    try:
        from graph_rag.rag_engine import graphrag_chat
        from services.ai_logic import INTENT_LABELS_VI

        result = graphrag_chat(query=query, customer_id=req.customer_id)
        intent = result.get("intent", "general")

        return ChatResponse(
            answer        = result["answer"],
            intent        = intent,
            intent_label  = INTENT_LABELS_VI.get(intent, "Câu hỏi tổng quát"),
            sources_count = result.get("sources_count", 0),
            mode          = result.get("mode", "template"),
        )
    except Exception as e:
        logger.error(f"[Chat] Lỗi xử lý: {e}")
        raise HTTPException(500, f"Lỗi xử lý câu hỏi: {str(e)}")


@app.post("/api/intent", tags=["AI Chat"])
def detect_intent(req: IntentRequest):
    """Phân loại intent câu hỏi (debug endpoint)."""
    from services.ai_logic import classify_medical_intent, INTENT_LABELS_VI
    intent = classify_medical_intent(req.query)
    return {
        "query":        req.query,
        "intent":       intent,
        "intent_label": INTENT_LABELS_VI.get(intent, "Không xác định"),
    }


@app.get("/api/kb/stats", tags=["Knowledge Base"])
def kb_stats():
    """Thống kê knowledge base."""
    from graph_rag.rag_engine import _faiss_chunks, _faiss_index, NEO4J_AVAILABLE
    return {
        "faiss_chunks":  len(_faiss_chunks),
        "faiss_index":   "ready" if _faiss_index is not None else "not_built",
        "neo4j":         "available" if NEO4J_AVAILABLE else "unavailable",
        "kb_initialized": _kb_initialized,
    }


@app.post("/api/kb/build", tags=["Knowledge Base"])
def build_kb(background_tasks: BackgroundTasks):
    """Rebuild FAISS index từ medical knowledge base (chạy nền)."""
    def _rebuild():
        from graph_rag.rag_engine import build_faiss_index
        build_faiss_index(MEDICAL_KNOWLEDGE_BASE)
        logger.info("[KB] Rebuild hoàn thành.")

    background_tasks.add_task(_rebuild)
    return {"status": "triggered", "message": "KB rebuild đang chạy nền."}


@app.get("/api/graph/query", tags=["Graph"])
def graph_query(symptom: str = "đau dạ dày"):
    """Debug: truy vấn Neo4j trực tiếp theo triệu chứng."""
    from graph_rag.rag_engine import neo4j_query_symptom
    results = neo4j_query_symptom([symptom])
    return {"symptom": symptom, "graph_results": results, "count": len(results)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
