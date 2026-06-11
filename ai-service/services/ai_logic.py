"""
ai_logic.py – ai-consulting-service / services/
=================================================
Module xử lý logic AI cho chatbot tư vấn y tế:

1. classify_medical_intent() – Phân loại intent của câu hỏi người dùng
2. inject_medical_disclaimer() – Thêm cảnh báo y tế vào mọi response
3. format_graph_context()    – Format dữ liệu từ Neo4j thành context cho LLM
4. format_product_context()  – Format thông tin sản phẩm từ product-service
"""
import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# 1. INTENT CLASSIFICATION
# ══════════════════════════════════════════════════════════════════════════════

INTENT_PATTERNS = {
    "emergency": [
        r"cấp cứu", r"nguy hiểm", r"khẩn cấp", r"không thở", r"ngất xỉu",
        r"đột quỵ", r"nhồi máu", r"xuất huyết", r"emergency",
    ],
    "symptom_query": [
        r"tôi bị", r"đau", r"nhức", r"khó chịu", r"buồn nôn", r"tiêu chảy",
        r"táo bón", r"ợ chua", r"đầy bụng", r"chướng bụng", r"nôn", r"ói",
        r"triệu chứng", r"dấu hiệu", r"biểu hiện",
    ],
    "drug_info": [
        r"thuốc gì", r"uống thuốc", r"dùng thuốc", r"tác dụng của",
        r"công dụng", r"chỉ định", r"tác dụng phụ", r"contraindication",
        r"hoạt chất", r"thành phần",
    ],
    "dosage_query": [
        r"liều lượng", r"uống bao nhiêu", r"mấy viên", r"mấy lần",
        r"liều dùng", r"cách uống", r"cách dùng", r"hướng dẫn",
    ],
    "price_query": [
        r"giá", r"bao nhiêu tiền", r"phí", r"chi phí", r"mua ở đâu",
        r"có bán", r"còn hàng",
    ],
    "recommendation": [
        r"gợi ý", r"nên dùng", r"khuyên dùng", r"phù hợp", r"tốt nhất",
        r"nên uống", r"loại nào", r"dùng gì", r"recommend",
    ],
    "disease_info": [
        r"bệnh gì", r"viêm", r"loét", r"trào ngược", r"helicobacter",
        r"h\.pylori", r"gastritis", r"ulcer", r"reflux",
    ],
}


def classify_medical_intent(query: str) -> str:
    """
    Phân loại intent của câu hỏi y tế.

    Priority: emergency > symptom_query > drug_info > dosage_query
              > disease_info > recommendation > price_query > general

    Args:
        query: Câu hỏi từ người dùng

    Returns:
        Intent string: 'emergency' | 'symptom_query' | 'drug_info' |
                       'dosage_query' | 'price_query' | 'recommendation' |
                       'disease_info' | 'general'
    """
    query_lower = query.lower()

    # Kiểm tra từng intent theo thứ tự ưu tiên
    priority_order = [
        "emergency", "symptom_query", "drug_info", "dosage_query",
        "disease_info", "recommendation", "price_query",
    ]

    for intent in priority_order:
        patterns = INTENT_PATTERNS.get(intent, [])
        for pattern in patterns:
            if re.search(pattern, query_lower):
                logger.debug(f"[Intent] '{query[:50]}' → {intent}")
                return intent

    return "general"


INTENT_LABELS_VI = {
    "emergency":       "🚨 Tình huống khẩn cấp",
    "symptom_query":   "🤒 Hỏi về triệu chứng",
    "drug_info":       "💊 Thông tin thuốc",
    "dosage_query":    "📋 Hỏi liều lượng / cách dùng",
    "price_query":     "💰 Hỏi giá / mua hàng",
    "recommendation":  "⭐ Gợi ý sản phẩm",
    "disease_info":    "🏥 Thông tin bệnh lý",
    "general":         "💬 Câu hỏi tổng quát",
}


# ══════════════════════════════════════════════════════════════════════════════
# 2. MEDICAL DISCLAIMER
# ══════════════════════════════════════════════════════════════════════════════

DISCLAIMER_STANDARD = """

---
⚠️ **CẢNH BÁO Y TẾ QUAN TRỌNG:**
Thông tin trên chỉ mang tính chất tham khảo và KHÔNG thay thế cho tư vấn chuyên môn của bác sĩ hay dược sĩ. 
Vui lòng **tham khảo ý kiến bác sĩ hoặc dược sĩ** trước khi sử dụng bất kỳ thuốc nào, đặc biệt nếu bạn đang mang thai, cho con bú, hoặc có bệnh nền.
"""

DISCLAIMER_EMERGENCY = """

---
🚨 **TÌNH HUỐNG KHẨN CẤP:**
Nếu bạn hoặc người thân đang trong tình huống nguy hiểm đến tính mạng, vui lòng **GỌI NGAY 115** (Cấp cứu) hoặc đến cơ sở y tế gần nhất ngay lập tức.
Đừng chờ đợi hay tự điều trị.
"""


def inject_medical_disclaimer(response_text: str, intent: str = "general") -> str:
    """
    Thêm cảnh báo y tế phù hợp vào cuối response.

    Quy tắc:
    - intent='emergency' → disclaimer ngắn gọn + số điện thoại cấp cứu 115
    - Các intent khác → disclaimer tiêu chuẩn

    Args:
        response_text: Nội dung response chưa có disclaimer
        intent: Intent đã được phân loại

    Returns:
        Response + disclaimer phù hợp
    """
    if intent == "emergency":
        return response_text + DISCLAIMER_EMERGENCY
    return response_text + DISCLAIMER_STANDARD


# ══════════════════════════════════════════════════════════════════════════════
# 3. CONTEXT FORMATTING
# ══════════════════════════════════════════════════════════════════════════════

def format_graph_context(graph_results: List[Dict]) -> str:
    """
    Chuyển kết quả truy vấn Neo4j thành đoạn văn bản context cho LLM prompt.

    Dữ liệu đầu vào (ví dụ):
        [{"symptom": "Đau dạ dày", "disease": "Viêm loét dạ dày",
          "product": "Omeprazole", "category": "PPI"}]

    Returns:
        Đoạn văn bản mô tả các mối quan hệ triệu chứng-bệnh-thuốc
    """
    if not graph_results:
        return ""

    lines = ["**Thông tin y tế từ Knowledge Graph:**"]
    for item in graph_results:
        symptom  = item.get('symptom')
        disease  = item.get('disease')
        product  = item.get('product')
        category = item.get('category')

        if symptom and disease:
            lines.append(f"- Triệu chứng **{symptom}** có thể chỉ ra bệnh: **{disease}**")
        if disease and product:
            lines.append(f"- Điều trị **{disease}** có thể dùng: **{product}** (nhóm: {category or 'N/A'})")

    return "\n".join(lines)


def format_product_context(products: List[Dict]) -> str:
    """
    Format danh sách sản phẩm từ product-service thành context cho LLM.
    """
    if not products:
        return ""

    lines = ["**Sản phẩm y tế hiện có tại nhà thuốc:**"]
    for p in products[:5]:  # Giới hạn 5 sản phẩm để tránh context quá dài
        name     = p.get('name',     'N/A')
        generic  = p.get('generic_name', '')
        price    = p.get('price',    'N/A')
        dosage   = p.get('dosage_strength', '')
        form     = p.get('dosage_form_display', p.get('dosage_form', ''))
        usage    = p.get('description', '')[:150]  # Cắt ngắn

        line = f"- **{name}** {dosage} ({form})"
        if generic:
            line += f" – Hoạt chất: {generic}"
        if price:
            line += f" – Giá: {float(price):,.0f} VND"
        if usage:
            line += f"\n  Công dụng: {usage}..."
        lines.append(line)

    return "\n".join(lines)


def format_faiss_context(chunks: List[str]) -> str:
    """Format các đoạn văn bản từ FAISS knowledge base."""
    if not chunks:
        return ""
    lines = ["**Tài liệu y khoa liên quan:**"]
    for i, chunk in enumerate(chunks[:3], 1):
        lines.append(f"{i}. {chunk}")
    return "\n".join(lines)


def build_llm_prompt(
    user_query: str,
    graph_context: str,
    product_context: str,
    faiss_context: str,
    intent: str,
) -> str:
    """
    Xây dựng prompt đầy đủ cho LLM (Gemini 1.5 Flash).

    Structure:
        [System Role] → [Context từ 3 nguồn] → [Câu hỏi] → [Yêu cầu trả lời]
    """
    sections = []

    # System role
    sections.append(
        "Bạn là trợ lý AI của nhà thuốc điện tử Health-Micro-AI. "
        "Nhiệm vụ của bạn là cung cấp thông tin y tế chính xác, dễ hiểu dựa trên "
        "tài liệu y khoa và knowledge graph của hệ thống. "
        "Luôn nhắc người dùng tham khảo bác sĩ cho các quyết định điều trị quan trọng.\n"
    )

    # Đặt context từ 3 nguồn
    if graph_context:
        sections.append(graph_context)
    if product_context:
        sections.append(product_context)
    if faiss_context:
        sections.append(faiss_context)

    # Câu hỏi
    sections.append(f"\n**Câu hỏi của người dùng:** {user_query}")

    # Yêu cầu định dạng trả lời
    if intent == "emergency":
        sections.append(
            "\nHãy trả lời ngắn gọn, rõ ràng và ưu tiên an toàn tính mạng. "
            "Hướng dẫn gọi cấp cứu 115 nếu cần."
        )
    elif intent in ("symptom_query", "disease_info"):
        sections.append(
            "\nHãy giải thích triệu chứng/bệnh lý, gợi ý xét nghiệm cần thiết, "
            "và đề xuất nhóm thuốc phù hợp (nếu có)."
        )
    elif intent == "drug_info":
        sections.append(
            "\nHãy trình bày: công dụng, cơ chế tác động, tác dụng phụ thường gặp, "
            "và lưu ý quan trọng khi dùng thuốc."
        )
    else:
        sections.append("\nHãy trả lời đầy đủ, chính xác và dễ hiểu.")

    return "\n\n".join(sections)
