"""
seed_all.py – health-micro-ai
================================
Script khởi tạo toàn bộ môi trường dữ liệu cho hệ thống Healthcare E-commerce.

Sử dụng:
  python seed_all.py              # Chạy cả 3 phần
  python seed_all.py --part A    # Chỉ seed PostgreSQL (Django sản phẩm)
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


# ══════════════════════════════════════════════════════════════════════════════
# PART A – DJANGO PRODUCT SERVICE (PostgreSQL)
# 10 sản phẩm y tế về bệnh dạ dày
# ══════════════════════════════════════════════════════════════════════════════

STOMACH_PRODUCTS = [
    {
        "name":             "Phosphalugel",
        "generic_name":     "Aluminum Phosphate",
        "category":         "antacid",
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
        "category":         "ppi",
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
        "category":         "ppi",
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
        "category":         "h2_blocker",
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
        "category":         "antibiotic",
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
        "category":         "antibiotic",
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
        "category":         "mucosal",
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
        "category":         "antiemetic",
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
        "category":         "probiotic",
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
        "category":         "antispasmodic",
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
        if os.path.exists("benhdaday.csv"):
            with open("benhdaday.csv", "r", encoding="utf-8") as f:
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
        if os.path.exists("benhdaday.csv"):
            with open("benhdaday.csv", "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    chunk = f"Bệnh: {row.get('Tên Bệnh', '')} (ICD-10: {row.get('Mã số ICD-10', '')}). Triệu chứng: {row.get('Triệu chứng điển hình', '')}. Nguyên nhân: {row.get('Nguyên nhân chính', '')}. Chẩn đoán: {row.get('Phương pháp chẩn đoán', '')}."
                    chunks.append(chunk)
    except Exception as e:
        logger.warning(f"Không thể đọc benhdaday.csv để seed FAISS: {e}")
        
    # Read faq.txt
    try:
        if os.path.exists("faq.txt"):
            with open("faq.txt", "r", encoding="utf-8") as f:
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
    Part C: Encode 32 đoạn văn y tế bằng SentenceTransformer và lưu vào FAISS index.
    Nguồn dữ liệu:
      - 5 đoạn kiến thức nền gốc
      - 7 đoạn từ benhdaday.csv (ICD-10 descriptions)
      - 8 đoạn từ faq.txt (chế độ ăn, dấu hiệu nguy hiểm, hướng dẫn thuốc)
    Tổng: 32 chunks, dim=384 (paraphrase-multilingual-MiniLM-L12-v2)
    """
    logger.info("=" * 60)
    logger.info("PART C: Seeding FAISS Vector Store")
    logger.info(f"Model: paraphrase-multilingual-MiniLM-L12-v2")
    logger.info(f"Output: {FAISS_OUTPUT_DIR}/")
    logger.info("=" * 60)

    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except ImportError:
        logger.error("Lỗi: Thiếu thư viện. Chạy: pip install sentence-transformers numpy")
        return 0

    try:
        import faiss
        FAISS_AVAILABLE = True
    except ImportError:
        logger.warning("Cảnh báo: faiss-cpu chưa cài. Sẽ lưu embeddings dạng numpy.")
        FAISS_AVAILABLE = False

    try:
        logger.info("🔄 Đang tải SentenceTransformer model...")
        model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        logger.info("✅ Model tải xong!")
    except Exception as e:
        logger.error(f"❌ Không tải được model: {e}")
        return 0

    # Load extra data from CSV and TXT
    paragraphs = MEDICAL_KNOWLEDGE_PARAGRAPHS.copy()
    paragraphs.extend(load_extra_faiss_chunks())

    # Encode all paragraphs
    logger.info(f"🔄 Encoding {len(paragraphs)} đoạn văn y tế...")
    embeddings = model.encode(
        paragraphs,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    embeddings = embeddings.astype("float32")
    logger.info(f"✅ Encoding xong! Shape: {embeddings.shape} (dim={embeddings.shape[1]})")

    # Tạo output directory
    os.makedirs(FAISS_OUTPUT_DIR, exist_ok=True)

    if FAISS_AVAILABLE:
        # Tạo FAISS index (IndexFlatIP = cosine similarity với normalized vectors)
        dim   = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)
        faiss.write_index(index, os.path.join(FAISS_OUTPUT_DIR, "medical.index"))
        logger.info(f"✅ FAISS index đã lưu: {FAISS_OUTPUT_DIR}/medical.index")
    else:
        # Fallback: lưu numpy array
        np.save(os.path.join(FAISS_OUTPUT_DIR, "medical_embeddings.npy"), embeddings)
        logger.info(f"✅ Embeddings numpy đã lưu: {FAISS_OUTPUT_DIR}/medical_embeddings.npy")

    # Lưu text chunks
    chunks_path = os.path.join(FAISS_OUTPUT_DIR, "chunks.json")
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(paragraphs, f, ensure_ascii=False, indent=2)
    logger.info(f"✅ Text chunks đã lưu: {chunks_path}")

    # Test search
    logger.info("\n🔍 Test semantic search: 'Thuốc điều trị đau dạ dày ợ chua'")
    test_emb = model.encode(["Thuốc điều trị đau dạ dày ợ chua"], normalize_embeddings=True)
    if FAISS_AVAILABLE:
        distances, indices = index.search(test_emb.astype("float32"), 2)
        for rank, (dist, idx) in enumerate(zip(distances[0], indices[0]), 1):
            chunk_preview = paragraphs[idx][:80].replace('\n', ' ')
            logger.info(f"  #{rank} (score={dist:.3f}): {chunk_preview}...")

    logger.info(f"\nPart C kết quả: {len(paragraphs)} đoạn văn đã được encode và lưu")
    return len(paragraphs)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRYPOINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Seed all data for health-micro-ai system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  python seed_all.py           # Chạy cả 3 phần
  python seed_all.py --part A  # Chỉ seed PostgreSQL (sản phẩm)
  python seed_all.py --part B  # Chỉ seed Neo4j (knowledge graph)
  python seed_all.py --part C  # Chỉ seed FAISS (vector store)
        """,
    )
    parser.add_argument("--part", choices=["A", "B", "C"], help="Phần cần chạy (A, B, hoặc C)")
    args = parser.parse_args()

    logger.info("╔══════════════════════════════════════════════════════════╗")
    logger.info("║       health-micro-ai – SEED ALL DATA SCRIPT            ║")
    logger.info("╚══════════════════════════════════════════════════════════╝\n")

    total_success = 0

    if args.part is None or args.part == "A":
        count = seed_part_a()
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
