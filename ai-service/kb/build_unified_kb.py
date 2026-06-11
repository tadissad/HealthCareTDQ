from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set

KB_DIR = Path(__file__).resolve().parent
SOURCE_DIR = KB_DIR / "sources"

PROMPT1_PATH = SOURCE_DIR / "prompt1.seed.json"
PROMPT2_PATH = SOURCE_DIR / "prompt2.seed.json"
PROMPT3_PATH = SOURCE_DIR / "prompt3.seed.json"
FAQ_PATH = SOURCE_DIR / "faq.seed.txt"
DISEASE_CSV_PATH = SOURCE_DIR / "benhdaday.seed.csv"

UNIFIED_KB_PATH = KB_DIR / "unified_kb.json"
KB_CHUNKS_PATH = KB_DIR / "kb_chunks.json"
NEO4J_PAYLOAD_PATH = KB_DIR / "neo4j_seed_payload.json"


@dataclass(frozen=True)
class CategoryDef:
    code: str
    label: str
    legacy_keys: List[str]


CATEGORY_DEFS: List[CategoryDef] = [
    CategoryDef("ulcer_hp_support", "Ho tro dieu tri Viem loet va HP", ["ulcer_hp", "ulcer_hp_support"]),
    CategoryDef("reflux_heartburn", "Giam trao nguoc va o chua", ["acid_reflux", "reflux_heartburn"]),
    CategoryDef("probiotic_digestion", "Men vi sinh va ho tro tieu hoa", ["probiotic_gut", "probiotics", "probiotic_digestion"]),
    CategoryDef("herbal_extract", "Tinh chat nghe va thao duoc", ["herbal_turmeric", "herbal", "herbal_extract"]),
    CategoryDef("stomach_nutrition", "Thuc pham va dinh duong da day", ["gut_nutrition", "nutrition", "stomach_nutrition"]),
    CategoryDef("equipment_device", "Dung cu va thiet bi ho tro", ["medical_device", "equipment", "equipment_device"]),
    CategoryDef("test_kit_home", "Bo xet nghiem va kiem tra tai nha", ["home_test", "testing_kits", "test_kit_home"]),
    CategoryDef("consultation_package", "Goi kham va tu van bac si", ["consult_package", "medical_services", "consultation_package"]),
    CategoryDef("elderly_weak_digestion", "Danh cho nguoi gia va he tieu hoa yeu", ["elderly_gut", "elderly_weak_gut", "elderly_weak_digestion"]),
    CategoryDef("vitamin_mineral", "Vitamin va khoang chat bo tro", ["vitamins", "vitamin_mineral"]),
]

CATEGORY_MAP: Dict[str, str] = {}
for category in CATEGORY_DEFS:
    for key in category.legacy_keys:
        CATEGORY_MAP[key] = category.code

CATEGORY_LABELS = {item.code: item.label for item in CATEGORY_DEFS}

SYNTHETIC_PRODUCTS: Dict[str, List[Dict]] = {
    "ulcer_hp_support": [
        {
            "name": "Rabeprazole HP Care 20mg",
            "generic_name": "Rabeprazole",
            "dosage_form": "tablet",
            "dosage_strength": "20mg",
            "manufacturer": "Torrent Pharma",
            "origin_country": "India",
            "price": 198000,
            "unit": "hop 14 vien",
            "description": "Thuoc ho tro giam acid cho phac do diet HP, phu hop nguoi hay dau thuong vi ban dem.",
            "symptom_tags": ["dau da day", "o chua", "nhiem hp"],
        },
        {
            "name": "Sucralfate Mucosa Shield 1g",
            "generic_name": "Sucralfate",
            "dosage_form": "sachet",
            "dosage_strength": "1g",
            "manufacturer": "Shinpoong",
            "origin_country": "Korea",
            "price": 176000,
            "unit": "hop 20 goi",
            "description": "Tao lop mang bao ve vet loet, ho tro phuc hoi niem mac da day trong giai doan cap.",
            "symptom_tags": ["viem loet da day", "dau thuong vi", "buon non"],
        },
    ],
    "reflux_heartburn": [
        {
            "name": "Esoplus Reflux 20mg",
            "generic_name": "Esomeprazole",
            "dosage_form": "capsule",
            "dosage_strength": "20mg",
            "manufacturer": "Sandoz",
            "origin_country": "Germany",
            "price": 149000,
            "unit": "hop 14 vien",
            "description": "Ho tro kiem soat trao nguoc, giam nong rat nguc va dang mieng vao buoi sang.",
            "symptom_tags": ["trao nguoc", "nong rat nguc", "dang mieng"],
        },
        {
            "name": "Alginate Reflux Barrier",
            "generic_name": "Sodium Alginate",
            "dosage_form": "suspension",
            "dosage_strength": "500mg/10ml",
            "manufacturer": "RB Health",
            "origin_country": "UK",
            "price": 165000,
            "unit": "chai 150ml",
            "description": "Tao mang gel ngan acid trao nguoc len thuc quan, dung sau bua an va truoc khi ngu.",
            "symptom_tags": ["o chua", "trao nguoc", "nuot nghen"],
        },
    ],
    "probiotic_digestion": [
        {
            "name": "LactoBalance IBS",
            "generic_name": "Lactobacillus + Bifidobacterium",
            "dosage_form": "capsule",
            "dosage_strength": "10B CFU",
            "manufacturer": "Biogaia",
            "origin_country": "Sweden",
            "price": 210000,
            "unit": "hop 30 vien",
            "description": "Can bang he vi sinh duong ruot, ho tro giam day bung va hoi chung ruot kich thich.",
            "symptom_tags": ["day bung", "kho tieu", "tao bon"],
        },
        {
            "name": "Digestzyme Plus",
            "generic_name": "Amylase + Protease",
            "dosage_form": "tablet",
            "dosage_strength": "250mg",
            "manufacturer": "DHG Pharma",
            "origin_country": "Vietnam",
            "price": 98000,
            "unit": "hop 20 vien",
            "description": "Bo sung enzyme tieu hoa cho nguoi hay day hoi sau an nhieu dam va dau mo.",
            "symptom_tags": ["kho tieu", "soi bung", "day hoi"],
        },
    ],
    "herbal_extract": [
        {
            "name": "Curcumin Forte Plus",
            "generic_name": "Nano Curcumin",
            "dosage_form": "capsule",
            "dosage_strength": "250mg",
            "manufacturer": "CVI Pharma",
            "origin_country": "Vietnam",
            "price": 255000,
            "unit": "hop 30 vien",
            "description": "Ho tro khang viem niem mac da day va giam dau rat sau cac bua an cay nong.",
            "symptom_tags": ["dau da day", "o hoi", "viem loet da day"],
        },
        {
            "name": "Che day Gastro Tea",
            "generic_name": "Che day extract",
            "dosage_form": "tea",
            "dosage_strength": "2g/goi",
            "manufacturer": "Bstar Herb",
            "origin_country": "Vietnam",
            "price": 89000,
            "unit": "hop 25 goi",
            "description": "Tra thao duoc ho tro lam diu niem mac va giam trieu chung kho tieu, dang mieng.",
            "symptom_tags": ["kho tieu", "dang mieng", "day bung"],
        },
    ],
    "stomach_nutrition": [
        {
            "name": "Gastro Protein Soup",
            "generic_name": "Hydrolyzed protein",
            "dosage_form": "powder",
            "dosage_strength": "350g",
            "manufacturer": "Nestle Health",
            "origin_country": "Switzerland",
            "price": 395000,
            "unit": "lon 350g",
            "description": "Dinh duong de hap thu cho nguoi viem loet da day, kem an va sut can.",
            "symptom_tags": ["chan an", "sut can", "met moi"],
        },
        {
            "name": "Low Acid Oat Meal Mix",
            "generic_name": "Oat beta-glucan",
            "dosage_form": "powder",
            "dosage_strength": "400g",
            "manufacturer": "Anvico",
            "origin_country": "Vietnam",
            "price": 122000,
            "unit": "hop 20 goi",
            "description": "Bot yen mach do acid thap, ho tro nguoi trao nguoc va dau da day luc doi.",
            "symptom_tags": ["dau da day luc doi", "trao nguoc", "kho tieu"],
        },
    ],
    "equipment_device": [
        {
            "name": "HeatPad Digest Comfort",
            "generic_name": "Heating pad",
            "dosage_form": "device",
            "dosage_strength": "40W",
            "manufacturer": "Beurer",
            "origin_country": "Germany",
            "price": 620000,
            "unit": "thiet bi",
            "description": "Dem chuom nong dieu nhiet giam co that bung va dau do lanh bung.",
            "symptom_tags": ["dau quan bung", "lanh bung", "chuong bung"],
        },
        {
            "name": "Reflux Sleep Wedge",
            "generic_name": "Sleep support pillow",
            "dosage_form": "device",
            "dosage_strength": "15 degree",
            "manufacturer": "Yorokobi",
            "origin_country": "Japan",
            "price": 480000,
            "unit": "chiec",
            "description": "Goi nem nang dau giuong giup han che trao nguoc ve dem va non tra.",
            "symptom_tags": ["trao nguoc ban dem", "o nong", "nuot nghen"],
        },
    ],
    "test_kit_home": [
        {
            "name": "HP Stool Antigen Rapid",
            "generic_name": "Helicobacter pylori Ag test",
            "dosage_form": "test_kit",
            "dosage_strength": "single test",
            "manufacturer": "Abbott",
            "origin_country": "USA",
            "price": 175000,
            "unit": "kit",
            "description": "Bo test nhanh HP qua phan tai nha, doc ket qua trong 10-15 phut.",
            "symptom_tags": ["nhiem hp", "hoi mieng", "dau thuong vi"],
        },
        {
            "name": "FOB Home Screening",
            "generic_name": "Fecal occult blood test",
            "dosage_form": "test_kit",
            "dosage_strength": "single test",
            "manufacturer": "Humasis",
            "origin_country": "Korea",
            "price": 92000,
            "unit": "kit",
            "description": "Kit sang loc mau an trong phan, canh bao som nguy co xuat huyet tieu hoa.",
            "symptom_tags": ["phan den", "met moi", "xuat huyet tieu hoa"],
        },
    ],
    "consultation_package": [
        {
            "name": "Telehealth GI Basic",
            "generic_name": "Online consultation",
            "dosage_form": "service",
            "dosage_strength": "30 minutes",
            "manufacturer": "HealthMicro",
            "origin_country": "Vietnam",
            "price": 199000,
            "unit": "goi",
            "description": "Goi tu van truc tuyen cho benh nhan dau da day, trao nguoc, ROI loan tieu hoa.",
            "symptom_tags": ["dau da day", "o chua", "kho tieu"],
        },
        {
            "name": "GI Endoscopy Package",
            "generic_name": "Digestive checkup",
            "dosage_form": "service",
            "dosage_strength": "single package",
            "manufacturer": "HealthMicro",
            "origin_country": "Vietnam",
            "price": 1299000,
            "unit": "goi",
            "description": "Goi noi soi da day khong dau va doc ket qua boi bac si tieu hoa.",
            "symptom_tags": ["dau da day khong dut", "sut can", "non ra mau"],
        },
    ],
    "elderly_weak_digestion": [
        {
            "name": "ElderDigest Fiber Soft",
            "generic_name": "FOS + Inulin",
            "dosage_form": "powder",
            "dosage_strength": "5g/goi",
            "manufacturer": "NutriCare",
            "origin_country": "Vietnam",
            "price": 128000,
            "unit": "hop 30 goi",
            "description": "Chat xo hoa tan danh cho nguoi cao tuoi hay tao bon va day bung lau ngay.",
            "symptom_tags": ["tao bon", "day bung", "chan an"],
        },
        {
            "name": "Senior Probiotic 60+",
            "generic_name": "Lactobacillus rhamnosus",
            "dosage_form": "capsule",
            "dosage_strength": "5B CFU",
            "manufacturer": "Blackmores",
            "origin_country": "Australia",
            "price": 285000,
            "unit": "hop 30 vien",
            "description": "Men vi sinh cho nguoi lon tuoi, ho tro tieu hoa yeu va hap thu kem.",
            "symptom_tags": ["kho tieu", "tao bon", "met moi"],
        },
    ],
    "vitamin_mineral": [
        {
            "name": "Zinc B Complex Digest",
            "generic_name": "Zinc gluconate + B complex",
            "dosage_form": "tablet",
            "dosage_strength": "100mg",
            "manufacturer": "NatureMade",
            "origin_country": "USA",
            "price": 145000,
            "unit": "hop 30 vien",
            "description": "Bo sung kem va vitamin nhom B cho nguoi kem an, met moi do roi loan tieu hoa.",
            "symptom_tags": ["met moi", "chan an", "kho hap thu"],
        },
        {
            "name": "Electrolyte Rehydrate Plus",
            "generic_name": "ORS + minerals",
            "dosage_form": "sachet",
            "dosage_strength": "4.2g/goi",
            "manufacturer": "Mekophar",
            "origin_country": "Vietnam",
            "price": 68000,
            "unit": "hop 20 goi",
            "description": "Bo sung dien giai cho benh nhan tieu chay, non mua va mat nuoc nhe.",
            "symptom_tags": ["tieu chay", "non mua", "met moi"],
        },
    ],
}


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value or "")
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _normalize_category(category_key: str) -> str:
    if not category_key:
        return "stomach_nutrition"
    return CATEGORY_MAP.get(category_key, category_key if category_key in CATEGORY_LABELS else "stomach_nutrition")


def _split_faq_chunks(raw_text: str) -> List[str]:
    chunks: List[str] = []
    for part in raw_text.split("Câu "):
        part = part.strip()
        if not part:
            continue
        if not part[0].isdigit():
            continue
        cleaned = ("Câu " + part).replace("\n", " ")
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if len(cleaned) > 60:
            chunks.append(cleaned)
    return chunks


def _split_symptoms(text: str) -> List[str]:
    if not text:
        return []
    cleaned = text.replace(";", ",")
    parts = re.split(r",(?![^()]*\))", cleaned)
    output: List[str] = []
    for raw in parts:
        item = re.sub(r"\s+", " ", raw).strip(" .")
        if len(item) < 3 or len(item) > 140:
            continue
        if item.count("(") != item.count(")"):
            continue
        output.append(item)
    return output


def _load_disease_rows() -> List[Dict]:
    rows: List[Dict] = []
    with DISEASE_CSV_PATH.open("r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            rows.append(row)
    return rows


def _canonicalize_products(prompt_products: List[Dict]) -> List[Dict]:
    output: List[Dict] = []
    for item in prompt_products:
        category_code = _normalize_category(str(item.get("category", "")).strip())
        output.append(
            {
                "name": item.get("name", "").strip(),
                "generic_name": item.get("generic_name"),
                "category": category_code,
                "categories": [category_code],
                "dosage_form": item.get("dosage_form"),
                "dosage_strength": item.get("dosage_strength"),
                "manufacturer": item.get("manufacturer"),
                "origin_country": item.get("origin_country"),
                "price": item.get("price"),
                "unit": item.get("unit"),
                "stock_quantity": item.get("stock_quantity"),
                "description": item.get("description"),
                "side_effects": item.get("side_effects"),
                "contraindications": item.get("contraindications"),
                "usage_instruction": item.get("usage_instruction"),
                "requires_prescription": bool(item.get("requires_prescription", False)),
                "symptom_tags": item.get("symptom_tags", []),
                "source_refs": ["prompt1.seed.json"],
            }
        )
    return output


def _expand_products(products: List[Dict], target_total: int = 50, min_per_category: int = 5) -> List[Dict]:
    used_names: Set[str] = {item["name"] for item in products}
    counts = Counter(item["category"] for item in products)

    for category_code in CATEGORY_LABELS:
        for template in SYNTHETIC_PRODUCTS.get(category_code, []):
            if counts[category_code] >= min_per_category:
                break
            if template["name"] in used_names:
                continue
            new_item = {
                "name": template["name"],
                "generic_name": template["generic_name"],
                "category": category_code,
                "categories": [category_code],
                "dosage_form": template["dosage_form"],
                "dosage_strength": template["dosage_strength"],
                "manufacturer": template["manufacturer"],
                "origin_country": template["origin_country"],
                "price": template["price"],
                "unit": template["unit"],
                "stock_quantity": 120,
                "description": template["description"],
                "side_effects": "Can tham khao y kien bac si neu dang dung thuoc dac tri khac.",
                "contraindications": "Khong dung khi di ung voi thanh phan cua san pham.",
                "usage_instruction": "Dung theo huong dan tren nhan san pham hoac theo tu van y te.",
                "requires_prescription": category_code in {"ulcer_hp_support", "consultation_package"},
                "symptom_tags": template["symptom_tags"],
                "source_refs": ["synthetic.product_expansion.v1", "prompt1.seed.json", "prompt2.seed.json"],
            }
            products.append(new_item)
            used_names.add(new_item["name"])
            counts[category_code] += 1

    # If still missing target count, keep generating deterministic extras.
    synthetic_index = 1
    category_order = list(CATEGORY_LABELS.keys())
    while len(products) < target_total:
        category_code = category_order[(synthetic_index - 1) % len(category_order)]
        candidate_name = f"{category_code.replace('_', ' ').title()} Support {synthetic_index:02d}"
        synthetic_index += 1
        if candidate_name in used_names:
            continue
        item = {
            "name": candidate_name,
            "generic_name": "General digestive support",
            "category": category_code,
            "categories": [category_code],
            "dosage_form": "capsule",
            "dosage_strength": "standard",
            "manufacturer": "HealthMicro Lab",
            "origin_country": "Vietnam",
            "price": 99000,
            "unit": "hop 30 vien",
            "stock_quantity": 100,
            "description": "San pham bo tro he tieu hoa, duoc them de bao phu day du danh muc hoc tap.",
            "side_effects": "Theo doi dap ung co the khi su dung lan dau.",
            "contraindications": "Khong dung neu di ung thanh phan.",
            "usage_instruction": "Dung theo huong dan y te.",
            "requires_prescription": False,
            "symptom_tags": ["ho tro tieu hoa"],
            "source_refs": ["synthetic.product_fill.v1"],
        }
        products.append(item)
        used_names.add(candidate_name)

    return products


def _build_symptoms_and_diseases(prompt2: Dict, disease_rows: List[Dict]) -> Dict:
    symptom_map: Dict[str, Dict] = {}
    disease_map: Dict[str, Dict] = {}
    symptom_edges: Set[tuple] = set()

    for symptom in prompt2.get("symptoms", []):
        name = (symptom.get("name") or "").strip()
        if not name:
            continue
        symptom_map[name] = {
            "name": name,
            "name_en": symptom.get("name_en"),
            "aliases": symptom.get("aliases", []),
            "source_refs": ["prompt2.seed.json"],
        }

    for disease in prompt2.get("diseases", []):
        name = (disease.get("name") or "").strip()
        if not name:
            continue
        disease_map[name] = {
            "name": name,
            "icd_code": disease.get("icd_code"),
            "severity": disease.get("severity"),
            "description": disease.get("description"),
            "source_refs": ["prompt2.seed.json"],
        }
        for symptom_name in disease.get("indicates_symptoms", []):
            sym_name = symptom_name.strip()
            if not sym_name:
                continue
            symptom_map.setdefault(
                sym_name,
                {
                    "name": sym_name,
                    "name_en": None,
                    "aliases": [],
                    "source_refs": ["prompt2.seed.json"],
                },
            )
            symptom_edges.add((sym_name, name, "prompt2.seed.json"))

    for row in disease_rows:
        disease_name = (row.get("Tên Bệnh") or "").strip()
        if not disease_name:
            continue
        existing = disease_map.setdefault(
            disease_name,
            {
                "name": disease_name,
                "icd_code": row.get("Mã số ICD-10"),
                "severity": "medium",
                "description": "",
                "source_refs": [],
            },
        )
        existing["icd_code"] = existing.get("icd_code") or row.get("Mã số ICD-10")
        if not existing.get("description"):
            existing["description"] = f"Nguyen nhan: {row.get('Nguyên nhân chính', '')}. Chan doan: {row.get('Phương pháp chẩn đoán', '')}."
        if "benhdaday.seed.csv" not in existing["source_refs"]:
            existing["source_refs"].append("benhdaday.seed.csv")

        for symptom_name in _split_symptoms(row.get("Triệu chứng điển hình", "")):
            symptom_map.setdefault(
                symptom_name,
                {
                    "name": symptom_name,
                    "name_en": None,
                    "aliases": [],
                    "source_refs": ["benhdaday.seed.csv"],
                },
            )
            symptom_edges.add((symptom_name, disease_name, "benhdaday.seed.csv"))

    return {
        "symptoms": sorted(symptom_map.values(), key=lambda item: item["name"]),
        "diseases": sorted(disease_map.values(), key=lambda item: item["name"]),
        "symptom_edges": [
            {"symptom": edge[0], "disease": edge[1], "source": edge[2]} for edge in sorted(symptom_edges)
        ],
    }


def _index_products(products: List[Dict]) -> Dict[str, str]:
    normalized_index: Dict[str, str] = {}
    for item in products:
        name = item["name"].strip()
        normalized_index[_normalize_text(name)] = name
    return normalized_index


def _match_product_name(hint: str, index: Dict[str, str]) -> str | None:
    key = _normalize_text(hint)
    if key in index:
        return index[key]

    for normalized, name in index.items():
        if key and (key in normalized or normalized in key):
            return name
    return None


def _build_treatment_edges(products: List[Dict], prompt2: Dict, prompt3: List[Dict]) -> List[Dict]:
    product_index = _index_products(products)
    edges: Dict[tuple, Dict] = {}

    for mapping in prompt2.get("product_mappings", []):
        disease_name = mapping.get("disease_name", "").strip()
        priority = int(mapping.get("priority", 2))
        category_code = _normalize_category(mapping.get("category_key", ""))
        for hint in mapping.get("product_names", []):
            matched = _match_product_name(hint, product_index)
            if not matched:
                continue
            key = (disease_name, matched)
            edges[key] = {
                "disease": disease_name,
                "product": matched,
                "priority": priority,
                "category": category_code,
                "source": "prompt2.seed.json",
            }

    # Recover additional links from prompt3 product hints
    for qa in prompt3:
        disease_hint = qa.get("topic", "").strip()
        for hint in qa.get("product_hints", []):
            matched = _match_product_name(hint, product_index)
            if not matched:
                continue
            # Only attach to known diseases if topic is not disease-like.
            for disease_name in [
                "Viêm loét dạ dày",
                "Trào ngược dạ dày thực quản (GERD)",
                "Rối loạn tiêu hóa",
            ]:
                if _normalize_text(disease_name).split(" ")[0] in _normalize_text(disease_hint):
                    key = (disease_name, matched)
                    edges.setdefault(
                        key,
                        {
                            "disease": disease_name,
                            "product": matched,
                            "priority": 3,
                            "category": _normalize_category(qa.get("category", "")),
                            "source": "prompt3.seed.json",
                        },
                    )

    return sorted(edges.values(), key=lambda item: (item["disease"], item["priority"], item["product"]))


def _build_chunks(products: List[Dict], symptoms: List[Dict], diseases: List[Dict], prompt3: List[Dict], faq_text: str) -> List[Dict]:
    chunks: List[Dict] = []

    for item in products:
        chunks.append(
            {
                "text": (
                    f"San pham: {item['name']}. Danh muc: {item['category']}. "
                    f"Mo ta: {item.get('description', '')} Trieu chung goi y: {', '.join(item.get('symptom_tags', []))}."
                ).strip(),
                "type": "product",
                "source": "|".join(item.get("source_refs", [])),
                "tags": [item["category"]],
            }
        )

    for disease in diseases:
        chunks.append(
            {
                "text": (
                    f"Benh: {disease['name']} (ICD: {disease.get('icd_code')}). "
                    f"Muc do: {disease.get('severity')}. Mo ta: {disease.get('description', '')}"
                ).strip(),
                "type": "disease",
                "source": "|".join(disease.get("source_refs", [])),
                "tags": ["disease"],
            }
        )

    for symptom in symptoms:
        alias_text = ", ".join(symptom.get("aliases", [])[:5])
        chunks.append(
            {
                "text": f"Trieu chung: {symptom['name']}. Alias: {alias_text}.",
                "type": "symptom",
                "source": "|".join(symptom.get("source_refs", [])),
                "tags": ["symptom"],
            }
        )

    for item in prompt3:
        chunk_text = (item.get("chunk") or "").strip()
        if not chunk_text:
            continue
        chunks.append(
            {
                "text": chunk_text,
                "type": "qa",
                "source": "prompt3.seed.json",
                "tags": [item.get("category", "general")],
            }
        )

    for faq_chunk in _split_faq_chunks(faq_text):
        chunks.append(
            {
                "text": faq_chunk,
                "type": "faq",
                "source": "faq.seed.txt",
                "tags": ["faq"],
            }
        )

    for index, chunk in enumerate(chunks, start=1):
        chunk["id"] = f"CHUNK_{index:05d}"

    return chunks


def build_unified_kb(target_products: int = 50) -> Dict:
    prompt1 = _read_json(PROMPT1_PATH)
    prompt2 = _read_json(PROMPT2_PATH)
    prompt3 = _read_json(PROMPT3_PATH)
    faq_text = FAQ_PATH.read_text(encoding="utf-8")
    disease_rows = _load_disease_rows()

    categories = [
        {
            "code": item.code,
            "name": item.label,
            "legacy_keys": item.legacy_keys,
            "source_refs": ["prompt2.seed.json", "data_user500.csv"],
        }
        for item in CATEGORY_DEFS
    ]

    products = _expand_products(_canonicalize_products(prompt1), target_total=target_products, min_per_category=5)
    medical = _build_symptoms_and_diseases(prompt2, disease_rows)
    treatment_edges = _build_treatment_edges(products, prompt2, prompt3)

    product_category_edges: List[Dict] = []
    for product in products:
        for category_code in product.get("categories", []):
            product_category_edges.append(
                {
                    "product": product["name"],
                    "category": category_code,
                    "source": "|".join(product.get("source_refs", [])),
                }
            )

    chunks = _build_chunks(products, medical["symptoms"], medical["diseases"], prompt3, faq_text)

    source_manifest = [
        {
            "file": "kb/sources/prompt1.seed.json",
            "purpose": "seed products",
            "used_for": ["products", "chunks", "neo4j"],
        },
        {
            "file": "kb/sources/prompt2.seed.json",
            "purpose": "taxonomy symptoms-diseases-mappings",
            "used_for": ["symptoms", "diseases", "neo4j", "chunks"],
        },
        {
            "file": "kb/sources/prompt3.seed.json",
            "purpose": "rich QA chunks",
            "used_for": ["chunks", "neo4j_hints"],
        },
        {
            "file": "kb/sources/benhdaday.seed.csv",
            "purpose": "disease clinical table",
            "used_for": ["diseases", "symptom_edges", "chunks"],
        },
        {
            "file": "kb/sources/faq.seed.txt",
            "purpose": "FAQ corpus",
            "used_for": ["chunks"],
        },
    ]

    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "builder": "ai-service/kb/build_unified_kb.py",
            "target_products": target_products,
            "actual_products": len(products),
            "sources": source_manifest,
        },
        "categories": categories,
        "products": products,
        "symptoms": medical["symptoms"],
        "diseases": medical["diseases"],
        "relations": {
            "symptom_indicates": medical["symptom_edges"],
            "disease_treated_by": treatment_edges,
            "product_belongs_to": product_category_edges,
        },
        "chunks": chunks,
    }


def write_outputs(payload: Dict) -> None:
    UNIFIED_KB_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    KB_CHUNKS_PATH.write_text(json.dumps(payload["chunks"], ensure_ascii=False, indent=2), encoding="utf-8")

    neo4j_payload = {
        "metadata": payload["metadata"],
        "categories": payload["categories"],
        "products": [
            {
                "name": item["name"],
                "category_codes": item.get("categories", []),
                "source_refs": item.get("source_refs", []),
            }
            for item in payload["products"]
        ],
        "symptoms": payload["symptoms"],
        "diseases": payload["diseases"],
        "relations": payload["relations"],
    }
    NEO4J_PAYLOAD_PATH.write_text(json.dumps(neo4j_payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build unified KB for ai-service")
    parser.add_argument("--target-products", type=int, default=50, help="Target total number of products")
    args = parser.parse_args()

    payload = build_unified_kb(target_products=args.target_products)
    write_outputs(payload)

    count_per_category = Counter(item["category"] for item in payload["products"])
    print("Unified KB build complete")
    print(f"- Products: {len(payload['products'])}")
    print(f"- Symptoms: {len(payload['symptoms'])}")
    print(f"- Diseases: {len(payload['diseases'])}")
    print(f"- Chunks: {len(payload['chunks'])}")
    print(f"- Unified KB: {UNIFIED_KB_PATH}")
    print(f"- Chunk file: {KB_CHUNKS_PATH}")
    print(f"- Neo4j payload: {NEO4J_PAYLOAD_PATH}")
    print("- Product distribution by category:")
    for code in CATEGORY_LABELS:
        print(f"  * {code}: {count_per_category.get(code, 0)}")


if __name__ == "__main__":
    main()
