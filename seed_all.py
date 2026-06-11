"""
seed_all.py – health-micro-ai
================================
Script khởi tạo toàn bộ môi trường dữ liệu cho hệ thống Healthcare E-commerce.

Sử dụng:
  python seed_all.py              # Chạy cả 4 phần
  python seed_all.py --part A    # Chỉ seed PostgreSQL (Django sản phẩm)
  python seed_all.py --part D    # Chỉ seed Medical Catalog (10 categories)
  python seed_all.py --part B    # Chỉ seed Neo4j (Knowledge Graph)
  python seed_all.py --part C    # Chỉ seed FAISS (Vector Store)

Yêu cầu:
  - Django services đang chạy (product-service trên port 8002)
  - Neo4j đang chạy (bolt://localhost:7687)
  - pip install neo4j faiss-cpu sentence-transformers requests

Tác giả: health-micro-ai team
"""

import os
import sys
import json
import time
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("seed_all")

# ── Config ─────────────────────────────────────────────────────────────────────
PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8002")
NEO4J_URI           = os.getenv("NEO4J_URI",           "bolt://localhost:7687")
NEO4J_USER          = os.getenv("NEO4J_USER",          "neo4j")
NEO4J_PASSWORD      = os.getenv("NEO4J_PASSWORD",      "health123")
FAISS_OUTPUT_DIR    = os.getenv("FAISS_OUTPUT_DIR",    "./faiss_seed_output")


def _resolve_source_path(file_name: str) -> str:
    candidates = [
        file_name,
        os.path.join("ai-service", "kb", "sources", file_name.replace(".csv", ".seed.csv").replace(".txt", ".seed.txt")),
        os.path.join("ai-service", "kb", "sources", file_name.replace(".json", ".seed.json")),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return file_name


# ══════════════════════════════════════════════════════════════════════════════
# PART A – DJANGO PRODUCT SERVICE (PostgreSQL)
# 10 sản phẩm y tế về bệnh dạ dày
# ══════════════════════════════════════════════════════════════════════════════

STOMACH_PRODUCTS = [
    {
        "name":             "Phosphalugel",
        "generic_name":     "Aluminum Phosphate",
        "category":         "ulcer_hp_support",
        "dosage_form":      "gel",
        "dosage_strength":  "20% gel",
        "manufacturer":     "Mayoly Spindler (Pháp)",
        "origin_country":   "Pháp",
        "price":            "45000",
        "unit":             "túi",
        "stock_quantity":   150,
        "description":      (
            "Thuốc kháng acid và bảo vệ niêm mạc dạ dày. Chỉ định: viêm loét dạ dày tá tràng, "
            "trào ngược dạ dày thực quản, đau thượng vị, ợ chua. "
            "Phosphalugel tạo lớp gel bảo vệ trực tiếp trên niêm mạc dạ dày."
        ),
        "side_effects":     "Táo bón (nếu dùng liều cao kéo dài). Hiếm gặp: tăng phosphate máu.",
        "contraindications": "Suy thận nặng. Thận trọng khi dùng dài hạn.",
        "usage_instruction": "Uống 1 gói (20g), 3 lần/ngày sau ăn 1 giờ và trước khi đi ngủ.",
        "requires_prescription": False,
        "symptom_tags":     ["đau dạ dày", "ợ chua", "trào ngược", "viêm loét"],
    },
    {
        "name":             "Nexium 20mg",
        "generic_name":     "Esomeprazole Magnesium",
        "category":         "reflux_heartburn",
        "dosage_form":      "capsule",
        "dosage_strength":  "20mg",
        "manufacturer":     "AstraZeneca",
        "origin_country":   "Thụy Điển",
        "price":            "85000",
        "unit":             "hộp 14 viên",
        "stock_quantity":   200,
        "description":      (
            "Thuốc ức chế bơm proton (PPI) thế hệ mới. Chỉ định: loét dạ dày tá tràng, "
            "trào ngược dạ dày thực quản (GERD), hội chứng Zollinger-Ellison, "
            "và phối hợp diệt Helicobacter pylori. Hiệu quả vượt trội so với Omeprazole."
        ),
        "side_effects":     "Đau đầu, tiêu chảy, buồn nôn, đau bụng. Hiếm gặp: phát ban.",
        "contraindications": "Mẫn cảm với Esomeprazole hoặc các PPI khác.",
        "usage_instruction": "Uống 1 viên/ngày, trước bữa ăn sáng 30-60 phút. Không nhai hay bẻ viên.",
        "requires_prescription": True,
        "symptom_tags":     ["đau dạ dày", "ợ chua", "trào ngược", "viêm loét", "h.pylori"],
    },
    {
        "name":             "Omeprazole 20mg",
        "generic_name":     "Omeprazole",
        "category":         "reflux_heartburn",
        "dosage_form":      "capsule",
        "dosage_strength":  "20mg",
        "manufacturer":     "Stada Vietnam",
        "origin_country":   "Việt Nam",
        "price":            "35000",
        "unit":             "hộp 30 viên",
        "stock_quantity":   300,
        "description":      (
            "Thuốc ức chế bơm proton thế hệ 1. Chỉ định: loét dạ dày tá tràng, "
            "viêm thực quản trào ngược, kết hợp kháng sinh diệt H. pylori. "
            "Thuốc generic phổ biến, hiệu quả và chi phí thấp."
        ),
        "side_effects":     "Đau đầu, tiêu chảy, nôn. Dùng kéo dài: giảm hấp thu Mg2+, B12.",
        "contraindications": "Dị ứng Omeprazole. Không dùng cùng Clopidogrel.",
        "usage_instruction": "20mg × 1 lần/ngày trước ăn sáng. Điều trị loét: 4-8 tuần.",
        "requires_prescription": True,
        "symptom_tags":     ["đau dạ dày", "ợ chua", "viêm loét", "trào ngược"],
    },
    {
        "name":             "Ranitidine 150mg",
        "generic_name":     "Ranitidine HCl",
        "category":         "reflux_heartburn",
        "dosage_form":      "tablet",
        "dosage_strength":  "150mg",
        "manufacturer":     "Pymepharco",
        "origin_country":   "Việt Nam",
        "price":            "28000",
        "unit":             "hộp 100 viên",
        "stock_quantity":   250,
        "description":      (
            "Thuốc ức chế thụ thể H2 histamine, giảm tiết acid dạ dày. "
            "Chỉ định: loét dạ dày tá tràng, GERD, hội chứng Zollinger-Ellison. "
            "Phù hợp cho bệnh nhân không dung nạp PPI hoặc cần điều trị ngắn hạn."
        ),
        "side_effects":     "Đau đầu, chóng mặt, táo bón hoặc tiêu chảy.",
        "contraindications": "Suy thận nặng (cần giảm liều). Dị ứng Ranitidine.",
        "usage_instruction": "150mg × 2 lần/ngày (sáng và tối). Hoặc 300mg × 1 lần trước ngủ.",
        "requires_prescription": True,
        "symptom_tags":     ["đau dạ dày", "ợ chua", "viêm loét"],
    },
    {
        "name":             "Amoxicillin 500mg",
        "generic_name":     "Amoxicillin Trihydrate",
        "category":         "ulcer_hp_support",
        "dosage_form":      "capsule",
        "dosage_strength":  "500mg",
        "manufacturer":     "Mekophar",
        "origin_country":   "Việt Nam",
        "price":            "55000",
        "unit":             "hộp 100 viên",
        "stock_quantity":   180,
        "description":      (
            "Kháng sinh penicillin phổ rộng. Trong điều trị bệnh dạ dày, "
            "được phối hợp trong phác đồ 3 thuốc hoặc 4 thuốc để diệt vi khuẩn "
            "Helicobacter pylori (H. pylori) – nguyên nhân hàng đầu gây loét dạ dày. "
            "Phác đồ chuẩn: Amoxicillin 1g + Clarithromycin 500mg + PPI × 14 ngày."
        ),
        "side_effects":     "Tiêu chảy, buồn nôn, phát ban. Nguy cơ: phản ứng phản vệ (hiếm).",
        "contraindications": "Dị ứng penicillin. Thận trọng với người suy thận.",
        "usage_instruction": "1g (2 viên 500mg) × 2 lần/ngày trong phác đồ diệt H. pylori. Uống trong 14 ngày.",
        "requires_prescription": True,
        "symptom_tags":     ["h.pylori", "viêm loét", "nhiễm khuẩn dạ dày"],
    },
    {
        "name":             "Metronidazole 500mg",
        "generic_name":     "Metronidazole",
        "category":         "ulcer_hp_support",
        "dosage_form":      "tablet",
        "dosage_strength":  "500mg",
        "manufacturer":     "Dược phẩm TW1",
        "origin_country":   "Việt Nam",
        "price":            "42000",
        "unit":             "hộp 100 viên",
        "stock_quantity":   150,
        "description":      (
            "Kháng sinh và kháng ký sinh trùng nhóm Nitroimidazole. "
            "Trong điều trị dạ dày: phối hợp phác đồ 4 thuốc diệt H. pylori "
            "(Bismuth quadruple therapy) hoặc phác đồ thay thế khi thất bại với Clarithromycin. "
            "Cũng hiệu quả với viêm đại tràng do C. difficile."
        ),
        "side_effects":     "Buồn nôn, vị kim loại trong miệng, tiêu chảy. Tránh uống rượu.",
        "contraindications": "Tam cá nguyệt đầu thai kỳ. Không uống cùng rượu (phản ứng Antabuse).",
        "usage_instruction": "500mg × 3 lần/ngày trong 7-14 ngày. Uống trong bữa ăn để giảm tác dụng phụ.",
        "requires_prescription": True,
        "symptom_tags":     ["h.pylori", "viêm loét", "nhiễm khuẩn dạ dày"],
    },
    {
        "name":             "Smecta 3g",
        "generic_name":     "Diosmectite",
        "category":         "elderly_weak_digestion",
        "dosage_form":      "sachet",
        "dosage_strength":  "3g/gói",
        "manufacturer":     "Ipsen (Pháp)",
        "origin_country":   "Pháp",
        "price":            "38000",
        "unit":             "hộp 30 gói",
        "stock_quantity":   200,
        "description":      (
            "Thuốc bảo vệ niêm mạc tiêu hóa, hấp phụ vi khuẩn và độc tố. "
            "Chỉ định: tiêu chảy cấp và mãn tính, đau và khó chịu đường tiêu hóa, "
            "viêm dạ dày ruột. Cơ chế: tạo lớp bảo vệ niêm mạc, không hấp thu vào máu → "
            "an toàn cho trẻ em và phụ nữ có thai."
        ),
        "side_effects":     "Táo bón (hiếm). Không có tác dụng phụ hệ thống.",
        "contraindications": "Tắc ruột (chống chỉ định). Thận trọng khi dùng cùng thuốc khác (hấp phụ).",
        "usage_instruction": "Người lớn: 3 gói/ngày. Hòa tan 1 gói vào nửa ly nước, uống trước bữa ăn.",
        "requires_prescription": False,
        "symptom_tags":     ["tiêu chảy", "đau bụng", "viêm dạ dày ruột", "khó tiêu"],
    },
    {
        "name":             "Domperidone 10mg",
        "generic_name":     "Domperidone Maleate",
        "category":         "elderly_weak_digestion",
        "dosage_form":      "tablet",
        "dosage_strength":  "10mg",
        "manufacturer":     "DHG Pharma",
        "origin_country":   "Việt Nam",
        "price":            "32000",
        "unit":             "hộp 100 viên",
        "stock_quantity":   220,
        "description":      (
            "Thuốc chống nôn và điều hòa nhu động dạ dày (prokinetic). "
            "Cơ chế: ức chế thụ thể Dopamine D2 ngoại biên → tăng trương lực cơ vòng thực quản dưới, "
            "thúc đẩy làm rỗng dạ dày. Chỉ định: buồn nôn, nôn, đầy bụng, chậm làm rỗng dạ dày, "
            "trào ngược dạ dày thực quản."
        ),
        "side_effects":     "Khô miệng, đau đầu, tăng prolactin (gynecomastia hiếm).",
        "contraindications": "Chảy máu dạ dày. Không dùng cùng thuốc kéo dài QT. Tránh dùng > 7 ngày.",
        "usage_instruction": "10mg × 3 lần/ngày, uống trước bữa ăn 15-30 phút. Tối đa 7 ngày.",
        "requires_prescription": False,
        "symptom_tags":     ["buồn nôn", "nôn", "đầy bụng", "chậm tiêu", "trào ngược"],
    },
    {
        "name":             "Lacidofil (Probiotic)",
        "generic_name":     "Lactobacillus rhamnosus + L. helveticus",
        "category":         "probiotic_digestion",
        "dosage_form":      "capsule",
        "dosage_strength":  "2×10⁹ CFU/viên",
        "manufacturer":     "Allergon AB (Thụy Điển)",
        "origin_country":   "Thụy Điển",
        "price":            "65000",
        "unit":             "hộp 20 viên",
        "stock_quantity":   100,
        "description":      (
            "Probiotic y tế kết hợp 2 chủng Lactobacillus sống. Chỉ định: "
            "phục hồi hệ vi sinh vật đường ruột sau kháng sinh, hỗ trợ điều trị tiêu chảy, "
            "hội chứng ruột kích thích (IBS), và phòng ngừa tái phát H. pylori. "
            "Mỗi viên chứa 2×10⁹ CFU vi khuẩn sống."
        ),
        "side_effects":     "Chướng bụng nhẹ trong vài ngày đầu (bình thường). Không có tác dụng phụ nghiêm trọng.",
        "contraindications": "Suy giảm miễn dịch nặng (cẩn thận). Dị ứng sữa (lactose).",
        "usage_instruction": (
            "2 viên/ngày, uống sau bữa ăn. Nếu dùng cùng kháng sinh: uống cách kháng sinh ít nhất 2 giờ. "
            "Bảo quản lạnh 2-8°C."
        ),
        "requires_prescription": False,
        "symptom_tags":     ["tiêu chảy", "sau kháng sinh", "ruột kích thích", "h.pylori hỗ trợ"],
    },
    {
        "name":             "Duspatalin 200mg",
        "generic_name":     "Mebeverine HCl",
        "category":         "elderly_weak_digestion",
        "dosage_form":      "capsule",
        "dosage_strength":  "200mg",
        "manufacturer":     "Abbott Healthcare (Hà Lan)",
        "origin_country":   "Hà Lan",
        "price":            "72000",
        "unit":             "hộp 30 viên",
        "stock_quantity":   130,
        "description":      (
            "Thuốc chống co thắt cơ trơn đường tiêu hóa, tác động trực tiếp lên cơ trơn ruột. "
            "Chỉ định: hội chứng ruột kích thích (IBS), co thắt đại tràng, đau bụng co thắt, "
            "chướng bụng. Ưu điểm: không ảnh hưởng nhu động ruột bình thường, ít tác dụng phụ "
            "hơn thuốc kháng cholinergic."
        ),
        "side_effects":     "Hiếm: ngứa, phù mặt, nổi mề đay (dị ứng).",
        "contraindications": "Tắc liệt ruột. Mẫn cảm Mebeverine.",
        "usage_instruction": "200mg × 2 lần/ngày (sáng và tối), uống trước bữa ăn 20 phút.",
        "requires_prescription": False,
        "symptom_tags":     ["đau bụng co thắt", "ruột kích thích", "chướng bụng", "đại tràng"],
    },
]


def seed_part_a():
    import requests as req
    logger.info('=' * 60)
    logger.info('PART A: Seeding pharmacy-service products (idempotent)')
    logger.info('=' * 60)
    existing_names = set()
    try:
        resp = req.get(PRODUCT_SERVICE_URL + '/products/', timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            items = data if isinstance(data, list) else data.get('results', [])
            existing_names = {item.get('name') for item in items if item.get('name')}
            logger.info('  [CHECK] %d products already in DB.' % len(existing_names))
    except Exception as e:
        logger.warning('  [CHECK] Could not fetch existing list: %s' % e)
    success_count = skip_count = fail_count = 0
    for i, product in enumerate(STOMACH_PRODUCTS, 1):
        if product['name'] in existing_names:
            logger.info('  [SKIP] %s already exists' % product['name'])
            skip_count += 1
            continue
        try:
            response = req.post(PRODUCT_SERVICE_URL + '/products/', json=product, timeout=10)
            if response.status_code in (200, 201):
                logger.info('  [OK] %s added' % product['name'])
                success_count += 1
            else:
                logger.warning('  [FAIL] %s HTTP %s' % (product['name'], response.status_code))
                fail_count += 1
        except Exception as e:
            logger.error('  [ERROR] %s - %s' % (product['name'], e))
            fail_count += 1
        import time as _t; _t.sleep(0.1)
    logger.info('Part A: %d created / %d skipped / %d failed' % (success_count, skip_count, fail_count))
    return success_count


# ══════════════════════════════════════════════════════════════════════════════
# PART B – NEO4J KNOWLEDGE GRAPH (Cypher Triples)
# ══════════════════════════════════════════════════════════════════════════════

NEO4J_CYPHER_STATEMENTS = [

    # ── Xóa dữ liệu cũ (optional, comment nếu muốn giữ) ──────────────────────
    "MATCH (n) DETACH DELETE n",

    # ── Tạo Constraints (đảm bảo unique) ─────────────────────────────────────
    "CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.name IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Symptom) REQUIRE s.name IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Disease) REQUIRE d.name IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE",

    # ── Tạo Nodes: Categories ─────────────────────────────────────────────────
    "MERGE (c:Category {name: 'Thuốc kháng acid'})",
    "MERGE (c:Category {name: 'PPI (Ức chế bơm proton)'})",
    "MERGE (c:Category {name: 'H2 Blocker'})",
    "MERGE (c:Category {name: 'Kháng sinh'})",
    "MERGE (c:Category {name: 'Probiotic'})",
    "MERGE (c:Category {name: 'Thuốc chống nôn'})",
    "MERGE (c:Category {name: 'Bảo vệ niêm mạc'})",
    "MERGE (c:Category {name: 'Chống co thắt'})",

    # ── Tạo Nodes: Symptoms ───────────────────────────────────────────────────
    "MERGE (s:Symptom {name: 'Đau dạ dày'})",
    "MERGE (s:Symptom {name: 'Ợ chua'})",
    "MERGE (s:Symptom {name: 'Đầy bụng'})",
    "MERGE (s:Symptom {name: 'Buồn nôn'})",
    "MERGE (s:Symptom {name: 'Nôn ói'})",
    "MERGE (s:Symptom {name: 'Tiêu chảy'})",
    "MERGE (s:Symptom {name: 'Táo bón'})",
    "MERGE (s:Symptom {name: 'Đau bụng co thắt'})",
    "MERGE (s:Symptom {name: 'Trào ngược acid'})",
    "MERGE (s:Symptom {name: 'Khó tiêu'})",

    # ── Tạo Nodes: Diseases ───────────────────────────────────────────────────
    "MERGE (d:Disease {name: 'Viêm loét dạ dày'})",
    "MERGE (d:Disease {name: 'Trào ngược dạ dày thực quản (GERD)'})",
    "MERGE (d:Disease {name: 'Nhiễm Helicobacter pylori (H. pylori)'})",
    "MERGE (d:Disease {name: 'Hội chứng ruột kích thích (IBS)'})",
    "MERGE (d:Disease {name: 'Viêm dạ dày cấp'})",
    "MERGE (d:Disease {name: 'Tiêu chảy cấp'})",

    # ── Tạo Nodes: Products ───────────────────────────────────────────────────
    "MERGE (p:Product {name: 'Phosphalugel', product_id: 1})",
    "MERGE (p:Product {name: 'Nexium 20mg',  product_id: 2})",
    "MERGE (p:Product {name: 'Omeprazole 20mg', product_id: 3})",
    "MERGE (p:Product {name: 'Ranitidine 150mg', product_id: 4})",
    "MERGE (p:Product {name: 'Amoxicillin 500mg', product_id: 5})",
    "MERGE (p:Product {name: 'Metronidazole 500mg', product_id: 6})",
    "MERGE (p:Product {name: 'Smecta 3g', product_id: 7})",
    "MERGE (p:Product {name: 'Domperidone 10mg', product_id: 8})",
    "MERGE (p:Product {name: 'Lacidofil (Probiotic)', product_id: 9})",
    "MERGE (p:Product {name: 'Duspatalin 200mg', product_id: 10})",

    # ── Tạo Nodes: Users ──────────────────────────────────────────────────────
    "MERGE (u:User {id: 'U123', name: 'Nguyễn Văn An'})",
    "MERGE (u:User {id: 'U124', name: 'Trần Thị Bình'})",
    "MERGE (u:User {id: 'U125', name: 'Lê Minh Cường'})",

    # ══════════════════════════════════════════════════════════════════════════
    # RELATIONSHIPS: Symptom -[:INDICATES]-> Disease
    # ══════════════════════════════════════════════════════════════════════════
    """MATCH (s:Symptom {name: 'Đau dạ dày'}), (d:Disease {name: 'Viêm loét dạ dày'})
    MERGE (s)-[:INDICATES]->(d)""",

    """MATCH (s:Symptom {name: 'Ợ chua'}), (d:Disease {name: 'Trào ngược dạ dày thực quản (GERD)'})
    MERGE (s)-[:INDICATES]->(d)""",

    """MATCH (s:Symptom {name: 'Trào ngược acid'}), (d:Disease {name: 'Trào ngược dạ dày thực quản (GERD)'})
    MERGE (s)-[:INDICATES]->(d)""",

    """MATCH (s:Symptom {name: 'Đau dạ dày'}), (d:Disease {name: 'Nhiễm Helicobacter pylori (H. pylori)'})
    MERGE (s)-[:INDICATES]->(d)""",

    """MATCH (s:Symptom {name: 'Đau bụng co thắt'}), (d:Disease {name: 'Hội chứng ruột kích thích (IBS)'})
    MERGE (s)-[:INDICATES]->(d)""",

    """MATCH (s:Symptom {name: 'Tiêu chảy'}), (d:Disease {name: 'Tiêu chảy cấp'})
    MERGE (s)-[:INDICATES]->(d)""",

    """MATCH (s:Symptom {name: 'Buồn nôn'}), (d:Disease {name: 'Viêm dạ dày cấp'})
    MERGE (s)-[:INDICATES]->(d)""",

    # ══════════════════════════════════════════════════════════════════════════
    # RELATIONSHIPS: Disease -[:TREATED_BY]-> Product
    # ══════════════════════════════════════════════════════════════════════════
    """MATCH (d:Disease {name: 'Viêm loét dạ dày'}), (p:Product {name: 'Phosphalugel'})
    MERGE (d)-[:TREATED_BY {priority: 1}]->(p)""",

    """MATCH (d:Disease {name: 'Viêm loét dạ dày'}), (p:Product {name: 'Omeprazole 20mg'})
    MERGE (d)-[:TREATED_BY {priority: 2}]->(p)""",

    """MATCH (d:Disease {name: 'Viêm loét dạ dày'}), (p:Product {name: 'Nexium 20mg'})
    MERGE (d)-[:TREATED_BY {priority: 3}]->(p)""",

    """MATCH (d:Disease {name: 'Trào ngược dạ dày thực quản (GERD)'}), (p:Product {name: 'Nexium 20mg'})
    MERGE (d)-[:TREATED_BY {priority: 1}]->(p)""",

    """MATCH (d:Disease {name: 'Trào ngược dạ dày thực quản (GERD)'}), (p:Product {name: 'Domperidone 10mg'})
    MERGE (d)-[:TREATED_BY {priority: 2}]->(p)""",

    """MATCH (d:Disease {name: 'Nhiễm Helicobacter pylori (H. pylori)'}), (p:Product {name: 'Amoxicillin 500mg'})
    MERGE (d)-[:TREATED_BY {priority: 1}]->(p)""",

    """MATCH (d:Disease {name: 'Nhiễm Helicobacter pylori (H. pylori)'}), (p:Product {name: 'Metronidazole 500mg'})
    MERGE (d)-[:TREATED_BY {priority: 2}]->(p)""",

    """MATCH (d:Disease {name: 'Nhiễm Helicobacter pylori (H. pylori)'}), (p:Product {name: 'Omeprazole 20mg'})
    MERGE (d)-[:TREATED_BY {priority: 3}]->(p)""",

    """MATCH (d:Disease {name: 'Hội chứng ruột kích thích (IBS)'}), (p:Product {name: 'Duspatalin 200mg'})
    MERGE (d)-[:TREATED_BY {priority: 1}]->(p)""",

    """MATCH (d:Disease {name: 'Hội chứng ruột kích thích (IBS)'}), (p:Product {name: 'Lacidofil (Probiotic)'})
    MERGE (d)-[:TREATED_BY {priority: 2}]->(p)""",

    """MATCH (d:Disease {name: 'Tiêu chảy cấp'}), (p:Product {name: 'Smecta 3g'})
    MERGE (d)-[:TREATED_BY {priority: 1}]->(p)""",

    """MATCH (d:Disease {name: 'Tiêu chảy cấp'}), (p:Product {name: 'Lacidofil (Probiotic)'})
    MERGE (d)-[:TREATED_BY {priority: 2}]->(p)""",

    # ══════════════════════════════════════════════════════════════════════════
    # RELATIONSHIPS: Product -[:BELONGS_TO]-> Category  (theo yêu cầu)
    # ══════════════════════════════════════════════════════════════════════════
    """MATCH (p:Product {name: 'Phosphalugel'}),    (c:Category {name: 'Thuốc kháng acid'})
    MERGE (p)-[:BELONGS_TO]->(c)""",

    """MATCH (p:Product {name: 'Nexium 20mg'}),     (c:Category {name: 'PPI (Ức chế bơm proton)'})
    MERGE (p)-[:BELONGS_TO]->(c)""",

    """MATCH (p:Product {name: 'Omeprazole 20mg'}), (c:Category {name: 'PPI (Ức chế bơm proton)'})
    MERGE (p)-[:BELONGS_TO]->(c)""",

    """MATCH (p:Product {name: 'Ranitidine 150mg'}),(c:Category {name: 'H2 Blocker'})
    MERGE (p)-[:BELONGS_TO]->(c)""",

    """MATCH (p:Product {name: 'Amoxicillin 500mg'}),(c:Category {name: 'Kháng sinh'})
    MERGE (p)-[:BELONGS_TO]->(c)""",

    """MATCH (p:Product {name: 'Metronidazole 500mg'}),(c:Category {name: 'Kháng sinh'})
    MERGE (p)-[:BELONGS_TO]->(c)""",

    """MATCH (p:Product {name: 'Smecta 3g'}),       (c:Category {name: 'Bảo vệ niêm mạc'})
    MERGE (p)-[:BELONGS_TO]->(c)""",

    """MATCH (p:Product {name: 'Domperidone 10mg'}),(c:Category {name: 'Thuốc chống nôn'})
    MERGE (p)-[:BELONGS_TO]->(c)""",

    """MATCH (p:Product {name: 'Lacidofil (Probiotic)'}),(c:Category {name: 'Probiotic'})
    MERGE (p)-[:BELONGS_TO]->(c)""",

    """MATCH (p:Product {name: 'Duspatalin 200mg'}),(c:Category {name: 'Chống co thắt'})
    MERGE (p)-[:BELONGS_TO]->(c)""",

    # ══════════════════════════════════════════════════════════════════════════
    # RELATIONSHIPS: User -[:SEARCHED {weight}]-> Symptom  (theo yêu cầu)
    # ══════════════════════════════════════════════════════════════════════════
    """MATCH (u:User {id: 'U123'}), (s:Symptom {name: 'Ợ chua'})
    MERGE (u)-[:SEARCHED {weight: 1, timestamp: datetime()}]->(s)""",

    """MATCH (u:User {id: 'U123'}), (s:Symptom {name: 'Đau dạ dày'})
    MERGE (u)-[:SEARCHED {weight: 3, timestamp: datetime()}]->(s)""",

    """MATCH (u:User {id: 'U124'}), (s:Symptom {name: 'Tiêu chảy'})
    MERGE (u)-[:SEARCHED {weight: 2, timestamp: datetime()}]->(s)""",

    """MATCH (u:User {id: 'U125'}), (s:Symptom {name: 'Đau bụng co thắt'})
    MERGE (u)-[:SEARCHED {weight: 2, timestamp: datetime()}]->(s)""",

    # ══════════════════════════════════════════════════════════════════════════
    # RELATIONSHIPS: User -[:PURCHASED]-> Product
    # ══════════════════════════════════════════════════════════════════════════
    """MATCH (u:User {id: 'U123'}), (p:Product {name: 'Phosphalugel'})
    MERGE (u)-[:PURCHASED {quantity: 2, date: date()}]->(p)""",

    """MATCH (u:User {id: 'U124'}), (p:Product {name: 'Smecta 3g'})
    MERGE (u)-[:PURCHASED {quantity: 1, date: date()}]->(p)""",
]


def load_extra_cypher():
    statements = []
    try:
        import csv
        benhdaday_path = _resolve_source_path("benhdaday.csv")
        if os.path.exists(benhdaday_path):
            with open(benhdaday_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    disease = row.get('Tên Bệnh', '').strip().replace("'", "")
                    icd = row.get('Mã số ICD-10', '').strip().replace("'", "")
                    symptoms = [s.strip().replace("'", "") for s in row.get('Triệu chứng điển hình', '').split(',')]
                    causes = [c.strip().replace("'", "") for c in row.get('Nguyên nhân chính', '').split(',')]
                    diagnostics = [d.strip().replace("'", "") for d in row.get('Phương pháp chẩn đoán', '').split(',')]
                    
                    if disease:
                        statements.append(f"MERGE (d:Disease {{name: '{disease}'}}) SET d.icd10 = '{icd}'")
                        for s in symptoms:
                            if s:
                                statements.append(f"MERGE (sym:Symptom {{name: '{s}'}})")
                                statements.append(f"MATCH (s:Symptom {{name: '{s}'}}), (d:Disease {{name: '{disease}'}}) MERGE (s)-[:INDICATES]->(d)")
                        for c in causes:
                            if c:
                                statements.append(f"MERGE (ca:Cause {{name: '{c}'}})")
                                statements.append(f"MATCH (ca:Cause {{name: '{c}'}}), (d:Disease {{name: '{disease}'}}) MERGE (ca)-[:CAUSES]->(d)")
                        for diag in diagnostics:
                            if diag:
                                statements.append(f"MERGE (di:Diagnostic {{name: '{diag}'}})")
                                statements.append(f"MATCH (d:Disease {{name: '{disease}'}}), (di:Diagnostic {{name: '{diag}'}}) MERGE (d)-[:DIAGNOSED_BY]->(di)")
    except Exception as e:
        logger.warning(f"Không thể tạo Cypher từ benhdaday.csv: {e}")
    return statements


def seed_part_b():
    """
    Part B: Seed Knowledge Graph vào Neo4j bằng Cypher queries.
    Neo4j phải đang chạy tại NEO4J_URI.
    """
    try:
        from neo4j import GraphDatabase
    except ImportError:
        logger.error("Lỗi: Thư viện neo4j chưa được cài. Chạy: pip install neo4j")
        return 0

    logger.info("=" * 60)
    logger.info("PART B: Seeding Knowledge Graph vào Neo4j")
    logger.info(f"Target: {NEO4J_URI} (user={NEO4J_USER})")
    logger.info("=" * 60)

    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        logger.info("✅ Kết nối Neo4j thành công!")
    except Exception as e:
        logger.error(f"❌ Không kết nối được Neo4j: {e}")
        logger.error("Hãy đảm bảo Neo4j đang chạy và credentials đúng.")
        return 0

    success = 0
    fail    = 0

    import copy
    all_stmts = copy.deepcopy(NEO4J_CYPHER_STATEMENTS)
    all_stmts.extend(load_extra_cypher())

    with driver.session() as session:
        for i, stmt in enumerate(all_stmts, 1):
            stmt_short = stmt.strip()[:80].replace('\n', ' ')
            try:
                session.run(stmt)
                logger.info(f"  ✅ [{i:03d}/{len(NEO4J_CYPHER_STATEMENTS)}] {stmt_short}...")
                success += 1
            except Exception as e:
                logger.warning(f"  ❌ [{i:03d}] {stmt_short}... → {e}")
                fail += 1

    driver.close()
    logger.info(f"\nPart B kết quả: {success} thành công / {fail} thất bại")
    return success


# ══════════════════════════════════════════════════════════════════════════════
# PART C – FAISS VECTOR STORE (Medical Knowledge Base)
# ══════════════════════════════════════════════════════════════════════════════

MEDICAL_KNOWLEDGE_PARAGRAPHS = [
    """Viêm loét dạ dày tá tràng (Peptic Ulcer Disease) là tình trạng niêm mạc dạ dày 
    hoặc tá tràng bị tổn thương, hình thành vết loét. Nguyên nhân phổ biến nhất là 
    vi khuẩn Helicobacter pylori (H. pylori) và việc sử dụng thuốc kháng viêm không 
    steroid (NSAIDs). Triệu chứng điển hình: đau bụng thượng vị, đau tăng khi đói,
    buồn nôn, ợ chua. Điều trị: kết hợp kháng sinh diệt H.pylori (Amoxicillin, 
    Clarithromycin, Metronidazole) và thuốc ức chế bơm proton PPI (Omeprazole, Esomeprazole).
    Phác đồ Triple therapy kéo dài 14 ngày có tỷ lệ diệt trừ H. pylori đến 80-90%.""",

    """Thuốc ức chế bơm proton (PPI - Proton Pump Inhibitors) là nhóm thuốc hiệu quả 
    nhất để điều trị các bệnh lý liên quan đến acid dạ dày. Cơ chế: ức chế enzyme 
    H+/K+-ATPase trên tế bào thành dạ dày, làm giảm tiết acid lên đến 90%. 
    Các PPI phổ biến: Omeprazole 20mg, Esomeprazole (Nexium) 20-40mg, Pantoprazole 40mg, 
    Lansoprazole 30mg. Tác dụng phụ thường gặp: đau đầu, tiêu chảy, buồn nôn. 
    Lưu ý: không dùng dài hạn vì nguy cơ loãng xương và thiếu vitamin B12.
    Nên uống trước bữa ăn 30-60 phút để đạt hiệu quả tối đa.""",

    """Trào ngược dạ dày thực quản (GERD - Gastroesophageal Reflux Disease) xảy ra khi 
    acid dạ dày trào ngược lên thực quản do cơ vòng thực quản dưới yếu hoặc giãn bất thường.
    Triệu chứng: ợ chua, ợ nóng (heartburn), đau ngực, khó nuốt, ho mãn tính. 
    Điều trị: thay đổi lối sống (giảm cân, không ăn trước khi ngủ 3 tiếng, tránh thức ăn 
    gây kích thích như cà phê, rượu, chocolate), dùng thuốc kháng acid (Phosphalugel, Maalox), 
    PPI (Nexium, Omeprazole), hoặc thuốc tăng nhu động (Domperidone, Metoclopramide).
    Trường hợp nặng có thể cần phẫu thuật Nissen fundoplication.""",

    """Hội chứng ruột kích thích (IBS - Irritable Bowel Syndrome) là rối loạn chức năng 
    đại tràng mãn tính, không có tổn thương thực thể. Triệu chứng: đau bụng, chướng bụng,
    tiêu chảy và/hoặc táo bón xen kẽ. Phân loại: IBS-D (tiêu chảy), IBS-C (táo bón), 
    IBS-M (hỗn hợp). Điều trị: thay đổi chế độ ăn (FODMAP thấp), probiotics 
    (Lactobacillus, Bifidobacterium), thuốc chống co thắt (Duspatalin/Mebeverine 200mg), 
    thuốc điều hòa nhu động ruột. Stress và lo âu là yếu tố kích hoạt quan trọng.
    Liệu pháp nhận thức hành vi (CBT) cũng cho thấy hiệu quả trong IBS.""",

    # 5 chunke kien thuc nen goc
    "Viem loet da day ta trang (Peptic Ulcer Disease): nguyen nhan chinh la H. pylori va NSAIDs. Trieu chung: dau thuong vi, oi chua, day bung. Phac do Triple therapy 14 ngay: PPI + Amoxicillin 1g + Clarithromycin 500mg. Ty le dieu tri thanh cong 80-90%.",

    "Thuoc uc che bom proton (PPI): Omeprazole, Esomeprazole (Nexium), Pantoprazole. Co che: uc che H+/K+-ATPase, giam tiet acid den 90%. Uong truoc bua an 30-60 phut. Khong dung dai han vi nguy co loang xuong, thieu B12.",

    "GERD (Trao nguoc da day thuc quan - K21): Co vong thuc quan duoi yeu, acid trao nguoc gay oi chua, oi nong, dau nguc, ho man tinh. Dieu tri: thay doi loi song, Phosphalugel, PPI (Nexium), Domperidone.",

    "IBS (Hoi chung ruot kich thich): Roi loan chuc nang dai trang man tinh. Trieu chung: dau bung, chuong bung, tieu chay/tao bon xen ke. Dieu tri: FODMAP thap, Lacidofil probiotic, Duspatalin/Mebeverine 200mg.",

    "H. pylori: vi khuan Gram am song trong acid da day nho enzyme urease. Nguyen nhan hang dau gay viem da day man tinh, loet da day, ung thu da day (WHO nhom I). Chan doan: Urea Breath Test, sinh thiet qua noi soi.",

    # 7 chunk tu benhdaday.csv
    "Benh: Viem loet da day - ta trang (ICD-10: K25, K26, K27). Trieu chung: dau thuong vi khi doi hoac sau bua an, day hoi, oi chua, nong rat vung nguc, phan den hoac co mau. Nguyen nhan: H. pylori, NSAIDs, loi song khong lanh manh. Chan doan: noi soi, test hoi tho, sinh thiet H. pylori.",

    "Benh: GERD - Trao nguoc da day thuc quan (ICD-10: K21). Trieu chung: vi chua trong mieng, nong rat thuong vi lan len hong, dau tuc nguc, ho keo dai, kho nuot. Nguyen nhan: suy giam co vong thuc quan, beo phi, nam ngay sau an, stress. Chan doan: noi soi.",

    "Benh: Xuat huyet da day (ICD-10: K92.2, K25.4, K26.4) - CAP CUU! Trieu chung: non ra mau do tuoi hoac nau den nhu ba ca phe, phan den hoi, met moi, chong mat, dau bung du doi. Nguyen nhan: bien chung viem loet, NSAIDs, bia ruou. GOI 115 NGAY!",

    "Benh: Ung thu da day (ICD-10: C16) - NGUY HIEM CAO. Trieu chung: dau thuong vi tang dan, an khong ngon, sut can nhanh, buon non, non co mau, phan den, chuong bung. SUT CAN NHANH + DAU THUONG VI LIEN TUC = DI KHAM NGAY!",

    "Benh: Viem da day ruot Gastroenteritis (ICD-10: A09, K52). Trieu chung: tieu chay, dau bung, buon non, non mua, sot, met moi. Nguyen nhan: Norovirus, rotavirus, E.coli, Salmonella, ky sinh trung, doc to. Xu ly: bu nuoc dien giai, Smecta, Lacidofil, nghi ngoi.",

    "Benh: Viem teo da day chuyen san tu mien (ICD-10: K29.4). Trieu chung: thieu mau hong cau to, met moi, suy nhuoc, bieu hien than kinh do thieu vitamin B12. Nguyen nhan: tu mien di truyen. Dieu tri: tiem bo sung Vitamin B12 dinh ky.",

    # 5 chunk FAQ an uong + thuoc
    "Che do an cho nguoi benh da day: Nen an com trang, khoai lang luoc, chao yen mach, rau la xanh, chuoi, tao nghien. Ca mon hap luoc nhu ga luoc, ca hap. Bo sung 25-30g chat xo hoa tan moi ngay. Sua chua chua probiotic giup can bang duong ruot.",

    "Thu pham can kieng khi benh da day: Chien ran nhieu dau mo, do an cay nong, ruou bia, ca phe, soda, caffeine kich thich da day va gay viem loet. Khong nam xuong ngay sau khi an. Uong du 1.5-2 lit nuoc moi ngay.",

    "Dau hieu nguy hiem can cap cuu: 1.Non ra mau do tuoi/nau den, 2.Phan den si/co mau tuoi, 3.Dau thuong vi du doi >2 tuan, 4.Hoa mat chong mat tut huyet ap, 5.Kho nuot nuot vuong, 6.Sut can nhanh chan an. GOI 115 NGAY!",

    "Huong dan dung thuoc: Khang axit uong 1-3h sau an va truoc ngu. Sucralfate uong 30-60 phut truoc an. PPI uong 30-60 phut truoc bua sang. Khang sinh diet H.pylori: phoi hop nhieu loai lien tuc 10-14 ngay. KHONG tu y dung thuoc khi thay don dau.",

    "Tac hai NSAIDs voi da day va tai phat H.pylori: NSAIDs (Ibuprofen, Diclofenac, Aspirin) uc che COX-1, pha hang rao bao ve niem mac. Neu bat buoc dung NSAIDs hay bao bac si de ke them PPI. Tai phat H.pylori do: dung khong du lieu, khang thuoc, van dung NSAIDs, hut thuoc la.",
]


def load_extra_faiss_chunks():
    chunks = []
    # Read benhdaday.csv
    try:
        import csv
        benhdaday_path = _resolve_source_path("benhdaday.csv")
        if os.path.exists(benhdaday_path):
            with open(benhdaday_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    chunk = f"Bệnh: {row.get('Tên Bệnh', '')} (ICD-10: {row.get('Mã số ICD-10', '')}). Triệu chứng: {row.get('Triệu chứng điển hình', '')}. Nguyên nhân: {row.get('Nguyên nhân chính', '')}. Chẩn đoán: {row.get('Phương pháp chẩn đoán', '')}."
                    chunks.append(chunk)
    except Exception as e:
        logger.warning(f"Không thể đọc benhdaday.csv để seed FAISS: {e}")
        
    # Read faq.txt
    try:
        faq_path = _resolve_source_path("faq.txt")
        if os.path.exists(faq_path):
            with open(faq_path, "r", encoding="utf-8") as f:
                content = f.read()
                parts = content.split("Câu ")
                for p in parts[1:]:
                    text = "Câu " + p.strip()
                    # Cleanup odd newlines with commas/periods
                    text = text.replace('\n', ' ').replace(' ,', ',').replace(' .', '.').replace('  ', ' ').strip()
                    if len(text) > 20:
                        chunks.append(text)
    except Exception as e:
        logger.warning(f"Không thể đọc faq.txt để seed FAISS: {e}")
        
    return chunks


def seed_part_c():
    """
    Part C: Encode doan van y te bang Gemini text-embedding-004 vao FAISS.
    Khong can SentenceTransformer hay PyTorch.
    """
    logger.info("=" * 60)
    logger.info("PART C: Seeding FAISS Vector Store (Gemini text-embedding-004)")
    logger.info("Model: google/text-embedding-004 (768-dim, API-based)")
    logger.info("Output: %s/" % FAISS_OUTPUT_DIR)
    logger.info("=" * 60)

    import numpy as np
    import time as _time

    try:
        import faiss
        FAISS_AVAIL = True
    except ImportError:
        logger.warning("faiss-cpu chua cai. Se luu numpy fallback.")
        FAISS_AVAIL = False

    from google import genai
    from google.genai import types as gtypes

    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if not gemini_key:
        try:
            with open(".env", encoding="utf-8") as ef:
                for line in ef:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY="):
                        gemini_key = line.split("=", 1)[1].strip()
                        break
        except Exception:
            pass

    if not gemini_key:
        logger.error("GEMINI_API_KEY chua duoc cau hinh. Khong the tao FAISS index.")
        return 0

    client = genai.Client(api_key=gemini_key)
    logger.info("[Gemini] API key ready. Dung gemini-embedding-001.")

    paragraphs = MEDICAL_KNOWLEDGE_PARAGRAPHS.copy()
    paragraphs.extend(load_extra_faiss_chunks())
    logger.info("Tong so chunks: %d" % len(paragraphs))

    embeddings = []
    failed = 0
    for i, chunk in enumerate(paragraphs):
        try:
            result = client.models.embed_content(
                model="gemini-embedding-001",
                contents=chunk,
                config=gtypes.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
            )
            emb = np.array(result.embeddings[0].values, dtype=np.float32)
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm
            embeddings.append(emb)
            if (i + 1) % 5 == 0:
                logger.info("  [%d/%d] encoded..." % (i + 1, len(paragraphs)))
            _time.sleep(0.05)
        except Exception as e:
            logger.warning("  [%d] Error: %s" % (i, e))
            failed += 1
            embeddings.append(np.zeros(768, dtype=np.float32))

    embeddings_matrix = np.vstack(embeddings).astype("float32")
    logger.info("Encoding xong! Shape: %s dim=%d" % (str(embeddings_matrix.shape), embeddings_matrix.shape[1]))

    os.makedirs(FAISS_OUTPUT_DIR, exist_ok=True)

    if FAISS_AVAIL:
        dim   = embeddings_matrix.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings_matrix)
        faiss.write_index(index, os.path.join(FAISS_OUTPUT_DIR, "medical.index"))
        logger.info("FAISS index saved: %s/medical.index" % FAISS_OUTPUT_DIR)

        try:
            test_result = client.models.embed_content(
                model="gemini-embedding-001",
                contents="Thuoc dieu tri dau da day o chua",
                config=gtypes.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
            )
            test_emb = np.array(test_result.embeddings[0].values, dtype=np.float32).reshape(1, -1)
            distances, indices = index.search(test_emb, 2)
            for rank, (dist, idx) in enumerate(zip(distances[0], indices[0]), 1):
                preview = paragraphs[idx][:80].replace(chr(10), " ")
                logger.info("  #%d (score=%.3f): %s..." % (rank, dist, preview))
        except Exception as e:
            logger.warning("Test search error: %s" % e)
    else:
        np.save(os.path.join(FAISS_OUTPUT_DIR, "medical_embeddings.npy"), embeddings_matrix)

    chunks_path = os.path.join(FAISS_OUTPUT_DIR, "chunks.json")
    with open(chunks_path, "w", encoding="utf-8") as f:
        import json as _json
        _json.dump(paragraphs, f, ensure_ascii=False, indent=2)
    logger.info("Chunks saved: %s" % chunks_path)
    logger.info("Part C: %d chunks encoded (%d failed)" % (len(paragraphs), failed))
    return len(paragraphs)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRYPOINT
# ══════════════════════════════════════════════════════════════════════════════

def seed_part_d():
    """
    Part D: Seed 10 categories vào medical-catalog-service
    Khởi tạo danh mục thuốc cấp cao và phân nhóm
    """
    import django
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'catalog_service.settings')
    django.setup()
    
    from app.models import MedicalCategory, SubCategory
    
    CATEGORIES = [
        {
            'name': 'Hỗ trợ Điều trị Viêm loét & HP',
            'code': 'ulcer_hp_support',
            'icon': '🩹',
            'description': 'Các sản phẩm hỗ trợ điều trị viêm loét dạ dày, tá tràng và nhiễm Helicobacter pylori',
            'subcategories': [
                {'name': 'Kháng sinh diệt H. pylori', 'code': 'antibiotics_hp', 'description': 'Amoxicillin, Metronidazole, Clarithromycin trong phác đồ diệt H. pylori', 'product_ids': [5, 6]},
                {'name': 'Bảo vệ niêm mạc & Chống acid', 'code': 'mucosal_protection', 'description': 'Phosphalugel, Smecta - bảo vệ trực tiếp niêm mạc dạ dày', 'product_ids': [1, 7]},
            ]
        },
        {
            'name': 'Giảm Trào ngược & Ợ chua',
            'code': 'reflux_heartburn',
            'icon': '🔥',
            'description': 'Các sản phẩm điều trị trào ngược dạ dày thực quản (GERD) và ợ chua',
            'subcategories': [
                {'name': 'Ức chế bơm proton (PPI)', 'code': 'ppi', 'description': 'Nexium (Esomeprazole), Omeprazole - giảm tiết acid đến 90%', 'product_ids': [2, 3]},
                {'name': 'Ức chế thụ thể H2', 'code': 'h2_blocker', 'description': 'Ranitidine - giảm tiết acid từ tế bào thành dạ dày', 'product_ids': [4]},
            ]
        },
        {
            'name': 'Men vi sinh & Hỗ trợ Tiêu hóa',
            'code': 'probiotic_digestion',
            'icon': '🦠',
            'description': 'Probiotics y tế hỗ trợ hệ vi sinh vật đường ruột, cân bằng tiêu hóa',
            'subcategories': [
                {'name': 'Probiotics chứng chỉ y tế', 'code': 'medical_probiotics', 'description': 'Lacidofil, Culturelle - Lactobacillus & Bifidobacterium sống', 'product_ids': [9]},
                {'name': 'Hỗ trợ sau kháng sinh', 'code': 'post_antibiotic', 'description': 'Phục hồi hệ vi sinh vật sau điều trị kháng sinh', 'product_ids': [9]},
            ]
        },
        {
            'name': 'Tinh chất Nghệ & Thảo dược',
            'code': 'herbal_extract',
            'icon': '🌿',
            'description': 'Chiết xuất từ thảo dược tự nhiên: Nghệ vàng, gừng, hoa cúc, cam thảo',
            'subcategories': [
                {'name': 'Tinh chất Nghệ vàng', 'code': 'turmeric_extract', 'description': 'Curcumin - chống viêm, hỗ trợ tiêu hóa tự nhiên', 'product_ids': []},
                {'name': 'Thảo dược kết hợp', 'code': 'herbal_blend', 'description': 'Hỗn hợp gừng, hoa cúc, cam thảo - giảm thổn không, hỗ trợ tiêu hóa', 'product_ids': []},
            ]
        },
        {
            'name': 'Thực phẩm & Dinh dưỡng Dạ dày',
            'code': 'stomach_nutrition',
            'icon': '🥗',
            'description': 'Sữa chuyên biệt, bột dinh dưỡng, thực phẩm chức năng cho dạ dày',
            'subcategories': [
                {'name': 'Sữa & Bột dinh dưỡng', 'code': 'nutrition_powder', 'description': 'Sữa chuyên biệt cho bệnh nhân dạ dày, bột mầm lúa mạch, cơm cháy', 'product_ids': []},
                {'name': 'Thực phẩm hỗ trợ tiêu hóa', 'code': 'digestive_food', 'description': 'Cơm lỏng, cháo ăn được, khoai lang luộc - dễ tiêu hóa', 'product_ids': []},
            ]
        },
        {
            'name': 'Dụng cụ & Thiết bị Hỗ trợ',
            'code': 'equipment_device',
            'icon': '⚙️',
            'description': 'Các thiết bị hỗ trợ điều trị: cốc nước ấm, máy nén, đệm hạt',
            'subcategories': [
                {'name': 'Thiết bị sưởi ấm', 'code': 'heating_device', 'description': 'Túi nước ấm, đệm sưởi - giảm đau co thắt', 'product_ids': []},
                {'name': 'Dụng cụ hỗ trợ uống thuốc', 'code': 'medication_device', 'description': 'Tách uống thuốc, dụng cụ nghiền hỗ trợ uống liều chiều', 'product_ids': []},
            ]
        },
        {
            'name': 'Bộ xét nghiệm & Kiểm tra tại nhà',
            'code': 'test_kit_home',
            'icon': '🧪',
            'description': 'Bộ test H. pylori tại nhà, test men gan, test máu độc lập',
            'subcategories': [
                {'name': 'Test H. pylori tại nhà', 'code': 'hp_test_home', 'description': 'Bộ test hơi thở H. pylori, test chất kéo dài (Urea Breath Test)', 'product_ids': []},
                {'name': 'Kit xét nghiệm máu & nước tiểu', 'code': 'blood_urine_test', 'description': 'Test men gan, test các chỉ số máu - kiểm tra sức khỏe cơ bản', 'product_ids': []},
            ]
        },
        {
            'name': 'Gói khám & Tư vấn Bác sĩ',
            'code': 'consultation_package',
            'icon': '👨‍⚕️',
            'description': 'Gói tư vấn trực tuyến, gói khám sức khỏe, gói follow-up',
            'subcategories': [
                {'name': 'Tư vấn trực tuyến với BS chuyên khoa', 'code': 'online_consultation', 'description': 'Video call 30 phút với bác sĩ tiêu hóa - tư vấn cá nhân hóa', 'product_ids': []},
                {'name': 'Gói khám & theo dõi định kỳ', 'code': 'follow_up_package', 'description': 'Gói khám 3 tháng - theo dõi tiến triển, điều chỉnh phác đồ', 'product_ids': []},
            ]
        },
        {
            'name': 'Dành cho Người già & Hệ tiêu hóa yếu',
            'code': 'elderly_weak_digestion',
            'icon': '👴',
            'description': 'Sản phẩm an toàn cho người cao tuổi, tiêu hóa yếu, dễ hấp thu',
            'subcategories': [
                {'name': 'Thuốc chống nôn & điều hòa nhu động', 'code': 'antiemetic_prokinetic', 'description': 'Domperidone - điều hòa dạ dày, an toàn cho người già', 'product_ids': [8]},
                {'name': 'Thuốc chống co thắt & giảm đau bụng', 'code': 'antispasmodic_pain', 'description': 'Duspatalin (Mebeverine) - chống co thắt, không ảnh hưởng nhu động bình thường', 'product_ids': [10]},
            ]
        },
        {
            'name': 'Vitamin & Khoáng chất Bổ trợ',
            'code': 'vitamin_mineral',
            'icon': '💊',
            'description': 'Bổ sung Vitamin B12, Vitamin D, Magnesium, Zinc - hỗ trợ miễn dịch & tiêu hóa',
            'subcategories': [
                {'name': 'Vitamin nhóm B & B12', 'code': 'vitamin_b_complex', 'description': 'Vitamin B12 - phòng ngừa thiếu máu sau dùng PPI dài hạn', 'product_ids': []},
                {'name': 'Khoáng chất: Mg, Zn, Ca', 'code': 'minerals', 'description': 'Magnesium, Zinc, Canxi - hỗ trợ hệ miễn dịch, xương', 'product_ids': []},
            ]
        },
    ]
    
    logger.info('=' * 60)
    logger.info('PART D: Seeding medical-catalog-service categories')
    logger.info('=' * 60)
    
    created_count = 0
    try:
        for cat_data in CATEGORIES:
            name = cat_data.pop('name')
            subcategories = cat_data.pop('subcategories')
            
            category, created = MedicalCategory.objects.get_or_create(
                code=cat_data['code'],
                defaults={'name': name, **cat_data}
            )
            
            if created:
                logger.info(f'  ✅ Created category: {category.name} ({category.code})')
                created_count += 1
            else:
                logger.info(f'  ⚠️  Category exists: {category.name} ({category.code})')
            
            for sub_data in subcategories:
                SubCategory.objects.get_or_create(
                    parent=category,
                    code=sub_data['code'],
                    defaults={
                        'name': sub_data['name'],
                        'description': sub_data['description'],
                        'product_ids': sub_data['product_ids'],
                    }
                )
        
        logger.info(f'\n✅ Part D: {created_count} categories created / {len(CATEGORIES)} total')
        return created_count
        
    except Exception as e:
        logger.error(f'❌ Part D failed: {e}')
        logger.error('Make sure medical-catalog-service is running and migrations are applied')
        return 0

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Seed all data for health-micro-ai system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  python seed_all.py           # Chạy cả 4 phần
  python seed_all.py --part A  # Chỉ seed PostgreSQL (sản phẩm)
  python seed_all.py --part D  # Chỉ seed Catalog (10 categories)
  python seed_all.py --part B  # Chỉ seed Neo4j (knowledge graph)
  python seed_all.py --part C  # Chỉ seed FAISS (vector store)
        """,
    )
    parser.add_argument("--part", choices=["A", "B", "C", "D"], help="Phần cần chạy (A, B, C, hoặc D)")
    args = parser.parse_args()

    logger.info("╔══════════════════════════════════════════════════════════╗")
    logger.info("║       health-micro-ai – SEED ALL DATA SCRIPT            ║")
    logger.info("╚══════════════════════════════════════════════════════════╝\n")

    total_success = 0

    if args.part is None or args.part == "A":
        count = seed_part_a()
        total_success += count
        print()

    if args.part is None or args.part == "D":
        count = seed_part_d()
        total_success += count
        print()

    if args.part is None or args.part == "B":
        count = seed_part_b()
        total_success += count
        print()

    if args.part is None or args.part == "C":
        count = seed_part_c()
        total_success += count
        print()

    logger.info("╔══════════════════════════════════════════════════════════╗")
    logger.info("║                  SEED HOÀN TẤT ✅                       ║")
    logger.info(f"║  Tổng đã xử lý: {total_success} objects                              ║")
    logger.info("╚══════════════════════════════════════════════════════════╝")

    logger.info("\nBước tiếp theo:")
    logger.info("  1. docker-compose up --build   # Khởi động toàn bộ hệ thống")
    logger.info("  2. Chờ tất cả service healthy (khoảng 2-3 phút)")
    logger.info("  3. python seed_all.py           # Chạy seed (nếu chưa chạy)")
    logger.info("  4. Mở http://localhost:8000     # API Gateway Web UI")
    logger.info("  5. GET http://localhost:8011/api/recommend/?user_id=U123")
    logger.info("  6. POST http://localhost:8013/api/chat   body: {\"message\": \"Tôi bị đau dạ dày\"}")


if __name__ == "__main__":
    main()
