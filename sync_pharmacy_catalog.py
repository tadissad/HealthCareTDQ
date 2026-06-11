from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List

import requests

DEFAULT_KB_PATH = Path("ai-service/kb/unified_kb.json")
DEFAULT_PHARMACY_URL = "http://localhost:8002"

# Match pharmacy-service CATEGORY_CHOICES.
VALID_CATEGORIES = {
    "ulcer_hp_support",
    "reflux_heartburn",
    "probiotic_digestion",
    "herbal_extract",
    "stomach_nutrition",
    "equipment_device",
    "test_kit_home",
    "consultation_package",
    "elderly_weak_digestion",
    "vitamin_mineral",
}

# Map legacy categories to the new canonical category codes.
LEGACY_CATEGORY_MAP = {
    "ulcer_hp": "ulcer_hp_support",
    "acid_reflux": "reflux_heartburn",
    "probiotic_gut": "probiotic_digestion",
    "probiotics": "probiotic_digestion",
    "herbal_turmeric": "herbal_extract",
    "herbal": "herbal_extract",
    "gut_nutrition": "stomach_nutrition",
    "nutrition": "stomach_nutrition",
    "medical_device": "equipment_device",
    "equipment": "equipment_device",
    "home_test": "test_kit_home",
    "testing_kits": "test_kit_home",
    "consult_package": "consultation_package",
    "medical_services": "consultation_package",
    "elderly_gut": "elderly_weak_digestion",
    "elderly_weak_gut": "elderly_weak_digestion",
    "vitamins": "vitamin_mineral",
}

# Match pharmacy-service DOSAGE_FORM_CHOICES.
VALID_DOSAGE_FORMS = {
    "tablet",
    "capsule",
    "syrup",
    "suspension",
    "sachet",
    "injection",
    "gel",
    "cream",
    "drops",
}

DOSAGE_FORM_MAP = {
    "powder": "sachet",
    "test_kit": "sachet",
    "device": "gel",
    "tea": "sachet",
    "service": "tablet",
}

_MOJIBAKE_MARKERS = ("Ã", "Â", "Ä", "á»", "áº")
_VI_PHRASE_MAP = [
    ("Can tham khao y kien bac si neu dang dung thuoc dac tri khac.", "Cần tham khảo ý kiến bác sĩ nếu đang dùng thuốc đặc trị khác."),
    ("Khong dung khi di ung voi thanh phan cua san pham.", "Không dùng khi dị ứng với thành phần của sản phẩm."),
    ("Dung theo huong dan tren nhan san pham hoac theo tu van y te.", "Dùng theo hướng dẫn trên nhãn sản phẩm hoặc theo tư vấn y tế."),
    ("dau da day", "đau dạ dày"),
    ("khong dut", "không dứt"),
    ("dau bung", "đau bụng"),
    ("dau thuong vi", "đau thượng vị"),
    ("o chua", "ợ chua"),
    ("nong rat", "nóng rát"),
    ("trao nguoc", "trào ngược"),
    ("viem loet", "viêm loét"),
    ("nhiem hp", "nhiễm HP"),
    ("kho tieu", "khó tiêu"),
    ("day bung", "đầy bụng"),
    ("buon non", "buồn nôn"),
    ("non mua", "nôn mửa"),
    ("tao bon", "táo bón"),
    ("tieu chay", "tiêu chảy"),
    ("met moi", "mệt mỏi"),
    ("dien giai", "điện giải"),
    ("benh nhan", "bệnh nhân"),
    ("mat nuoc", "mất nước"),
    ("nhe", "nhẹ"),
    ("kem an", "kém ăn"),
    ("roi loan", "rối loạn"),
    ("nguoi", "người"),
    ("yeu", "yếu"),
    ("hap thu", "hấp thu"),
    ("chat xo", "chất xơ"),
    ("hoa tan", "hòa tan"),
    ("danh cho", "dành cho"),
    ("lau ngay", "lâu ngày"),
    ("goi noi soi", "gói nội soi"),
    ("doc ket qua", "đọc kết quả"),
    ("boi bac si", "bởi bác sĩ"),
    ("khong dau", "không đau"),
    ("non ra mau", "nôn ra máu"),
    ("nuoc", "nước"),
    ("noi soi", "nội soi"),
    ("sut can", "sụt cân"),
    ("chan an", "chán ăn"),
    ("xuat huyet", "xuất huyết"),
    ("hoi mieng", "hôi miệng"),
    ("thao duoc", "thảo dược"),
    ("dinh duong", "dinh dưỡng"),
    ("tieu hoa", "tiêu hóa"),
    ("nguoi cao tuoi", "người cao tuổi"),
    ("nguoi lon tuoi", "người lớn tuổi"),
    ("ho tro", "hỗ trợ"),
    ("thuc pham", "thực phẩm"),
    ("bo sung", "bổ sung"),
    ("huong dan", "hướng dẫn"),
    ("tu van", "tư vấn"),
    ("y te", "y tế"),
    ("thanh phan", "thành phần"),
    ("bo sung kem", "bổ sung kẽm"),
]

_VI_TOKEN_MAP = {
    "goi": "gói",
    "hop": "hộp",
    "vien": "viên",
    "khong": "không",
    "dung": "dùng",
    "va": "và",
    "duoc": "dược",
    "da": "dạ",
    "day": "dày",
    "thuc": "thực",
    "pham": "phẩm",
    "nguoi": "người",
    "bac": "bác",
    "si": "sĩ",
    "lam": "làm",
    "diu": "dịu",
    "niem": "niêm",
    "mac": "mạc",
    "trieu": "triệu",
    "chung": "chứng",
    "dang": "đắng",
    "mieng": "miệng",
    "nhom": "nhóm",
    "lon": "lớn",
    "tuoi": "tuổi",
    "truc": "trực",
    "tuyen": "tuyến",
    "sang": "sàng",
    "loc": "lọc",
    "phan": "phân",
    "canh": "cảnh",
    "bao": "báo",
    "som": "sớm",
    "nguy": "nguy",
    "co": "cơ",
    "kho": "khó",
    "tra": "trà",
    "giam": "giảm",
    "mau": "máu",
    "an": "ẩn",
    "den": "đen",
}

_NAME_FIX_MAP = {
    "Che dày Gastro Tea": "Chè dây Gastro Tea",
    "Che day Gastro Tea": "Chè dây Gastro Tea",
    "Che dày extract": "Chè dây extract",
    "Che day extract": "Chè dây extract",
}

_ACCENTED_VI_CHARS = set(
    "ăâđêôơưáàảãạắằẳẵặấầẩẫậéèẻẽẹếềểễệ"
    "íìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ"
    "ĂÂĐÊÔƠƯÁÀẢÃẠẮẰẲẴẶẤẦẨẪẬÉÈẺẼẸẾỀỂỄỆ"
    "ÍÌỈĨỊÓÒỎÕỌỐỒỔỖỘỚỜỞỠỢÚÙỦŨỤỨỪỬỮỰÝỲỶỸỴ"
)

_CATEGORY_TEXT_TEMPLATES = {
    "ulcer_hp_support": {
        "description": "Sản phẩm hỗ trợ điều trị viêm loét dạ dày và nhiễm HP, giúp giảm đau thượng vị, ợ chua và phục hồi niêm mạc.",
        "usage_instruction": "Dùng theo hướng dẫn trên nhãn sản phẩm hoặc theo chỉ định của bác sĩ/dược sĩ.",
        "side_effects": "Có thể gặp khó chịu tiêu hóa nhẹ ở một số người dùng nhạy cảm.",
    },
    "reflux_heartburn": {
        "description": "Sản phẩm hỗ trợ giảm trào ngược dạ dày, ợ nóng và nóng rát vùng ngực.",
        "usage_instruction": "Nên dùng sau bữa ăn hoặc theo hướng dẫn chuyên môn để đạt hiệu quả tốt.",
        "side_effects": "Có thể gây đầy bụng nhẹ hoặc thay đổi tiêu hóa thoáng qua.",
    },
    "probiotic_digestion": {
        "description": "Sản phẩm hỗ trợ cân bằng hệ vi sinh đường ruột, giảm đầy bụng, khó tiêu và rối loạn tiêu hóa.",
        "usage_instruction": "Dùng đều đặn theo liều khuyến nghị; có thể uống sau ăn để dễ dung nạp.",
        "side_effects": "Hiếm gặp đầy hơi nhẹ trong giai đoạn đầu sử dụng.",
    },
    "herbal_extract": {
        "description": "Sản phẩm thảo dược hỗ trợ làm dịu niêm mạc dạ dày, giảm viêm và khó chịu vùng thượng vị.",
        "usage_instruction": "Dùng đúng liều theo nhãn; ưu tiên duy trì đều đặn để hỗ trợ lâu dài.",
        "side_effects": "Thường dung nạp tốt; ngưng dùng nếu có dấu hiệu dị ứng thành phần thảo dược.",
    },
    "stomach_nutrition": {
        "description": "Sản phẩm dinh dưỡng cho người có hệ tiêu hóa nhạy cảm, hỗ trợ phục hồi thể trạng và hấp thu.",
        "usage_instruction": "Dùng theo hướng dẫn pha/uống trên nhãn hoặc theo tư vấn dinh dưỡng.",
        "side_effects": "Có thể đầy bụng nhẹ nếu dùng quá nhanh hoặc quá liều khuyến nghị.",
    },
    "equipment_device": {
        "description": "Thiết bị hỗ trợ giảm khó chịu vùng bụng và theo dõi sức khỏe tiêu hóa tại nhà.",
        "usage_instruction": "Sử dụng đúng hướng dẫn an toàn của nhà sản xuất.",
        "side_effects": "Không có tác dụng phụ dược lý; lưu ý dùng đúng cách để tránh kích ứng cơ học.",
    },
    "test_kit_home": {
        "description": "Bộ kiểm tra tại nhà hỗ trợ sàng lọc nguy cơ bệnh lý tiêu hóa nhanh và tiện lợi.",
        "usage_instruction": "Đọc kỹ hướng dẫn lấy mẫu và thời gian đọc kết quả trước khi sử dụng.",
        "side_effects": "Không có tác dụng phụ dược lý vì chỉ dùng ngoài cơ thể.",
    },
    "consultation_package": {
        "description": "Gói khám/tư vấn giúp đánh giá tình trạng tiêu hóa và định hướng điều trị phù hợp.",
        "usage_instruction": "Đặt lịch trước và chuẩn bị hồ sơ y khoa liên quan để tư vấn chính xác hơn.",
        "side_effects": "Không có tác dụng phụ; đây là dịch vụ y tế hỗ trợ chẩn đoán và theo dõi.",
    },
    "elderly_weak_digestion": {
        "description": "Sản phẩm dành cho người cao tuổi hoặc người có hệ tiêu hóa yếu, hỗ trợ ăn ngon và hấp thu tốt hơn.",
        "usage_instruction": "Dùng đều theo liều khuyến nghị, kết hợp chế độ ăn mềm và dễ tiêu.",
        "side_effects": "Có thể xuất hiện khó chịu tiêu hóa nhẹ trong thời gian đầu.",
    },
    "vitamin_mineral": {
        "description": "Sản phẩm bổ sung vitamin và khoáng chất giúp nâng cao thể trạng, hỗ trợ phục hồi tiêu hóa.",
        "usage_instruction": "Uống theo liều khuyến nghị và nên dùng sau ăn để giảm kích ứng dạ dày.",
        "side_effects": "Một số sản phẩm có thể gây khó chịu nhẹ đường tiêu hóa nếu dùng lúc đói.",
    },
}


def _repair_mojibake_text(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""

    # Repair common UTF-8 text accidentally decoded as Latin-1/CP1252.
    if any(marker in text for marker in _MOJIBAKE_MARKERS):
        try:
            repaired = text.encode("latin-1", errors="strict").decode("utf-8", errors="strict")
            text = repaired
        except UnicodeError:
            pass

    text = re.sub(r"\s+", " ", text)
    for old, new in _VI_PHRASE_MAP:
        text = re.sub(re.escape(old), new, text, flags=re.IGNORECASE)

    # Contextual correction for zinc sentence fragments.
    text = re.sub(r"(?i)\b(bổ\s+sung)\s+kem\b", r"\1 kẽm", text)
    text = re.sub(r"(?i)\b(bo\s+sung)\s+kem\b", r"Bổ sung kẽm", text)

    # Apply token-level map with boundaries to avoid corrupting unrelated words.
    for old, new in _VI_TOKEN_MAP.items():
        text = re.sub(rf"\b{re.escape(old)}\b", new, text, flags=re.IGNORECASE)

    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    if text:
        text = text[0].upper() + text[1:]

    text = _NAME_FIX_MAP.get(text, text)

    # Uppercase first letter after sentence endings.
    text = re.sub(r"([\.!?]\s+)([a-zà-ỹ])", lambda m: m.group(1) + m.group(2).upper(), text)
    return text.strip()


def _repair_text_list(values: List[str]) -> List[str]:
    cleaned: List[str] = []
    for item in values or []:
        normalized = _repair_mojibake_text(str(item))
        if normalized:
            cleaned.append(normalized)
    return cleaned


def _is_mostly_unaccented_vi(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return True
    letters = [ch for ch in raw if ch.isalpha()]
    if not letters:
        return False
    accented = sum(1 for ch in letters if ch in _ACCENTED_VI_CHARS)
    # A low accented ratio is usually a signal this is synthetic Vietnamese without dấu.
    return accented / max(len(letters), 1) < 0.02


def _apply_template_fallback(payload: Dict) -> Dict:
    category = payload.get("category", "stomach_nutrition")
    template = _CATEGORY_TEXT_TEMPLATES.get(category, _CATEGORY_TEXT_TEMPLATES["stomach_nutrition"])

    for key in ("description", "usage_instruction", "side_effects"):
        value = (payload.get(key) or "").strip()
        if not value or _is_mostly_unaccented_vi(value):
            payload[key] = template[key]

    contraindications = (payload.get("contraindications") or "").strip()
    if not contraindications or _is_mostly_unaccented_vi(contraindications):
        payload["contraindications"] = "Không dùng khi dị ứng với bất kỳ thành phần nào của sản phẩm."

    return payload


def _normalize_category(raw: str) -> str:
    if not raw:
        return "stomach_nutrition"
    mapped = LEGACY_CATEGORY_MAP.get(raw, raw)
    return mapped if mapped in VALID_CATEGORIES else "stomach_nutrition"


def _normalize_dosage_form(raw: str) -> str:
    if not raw:
        return "tablet"
    mapped = DOSAGE_FORM_MAP.get(raw, raw)
    return mapped if mapped in VALID_DOSAGE_FORMS else "tablet"


def _to_payload(product: Dict) -> Dict:
    payload = {
        "name": _repair_mojibake_text(product.get("name", "Unnamed product")),
        "generic_name": _repair_mojibake_text(product.get("generic_name", "")),
        "category": _normalize_category(product.get("category", "")),
        "dosage_form": _normalize_dosage_form(product.get("dosage_form", "")),
        "dosage_strength": _repair_mojibake_text(product.get("dosage_strength", "") or ""),
        "manufacturer": _repair_mojibake_text(product.get("manufacturer", "") or ""),
        "origin_country": _repair_mojibake_text(product.get("origin_country", "") or ""),
        "price": product.get("price", 0) or 0,
        "unit": _repair_mojibake_text(product.get("unit", "hop") or "hop"),
        "stock_quantity": int(product.get("stock_quantity", 100) or 100),
        "description": _repair_mojibake_text(product.get("description", "") or ""),
        "side_effects": _repair_mojibake_text(product.get("side_effects", "") or ""),
        "contraindications": _repair_mojibake_text(product.get("contraindications", "") or ""),
        "usage_instruction": _repair_mojibake_text(product.get("usage_instruction", "") or ""),
        "requires_prescription": bool(product.get("requires_prescription", False)),
        "symptom_tags": _repair_text_list(product.get("symptom_tags", []) or []),
        "is_active": True,
    }
    payload = _apply_template_fallback(payload)
    payload["name"] = _NAME_FIX_MAP.get(payload["name"], payload["name"])
    return payload


def _load_unified_products(kb_path: Path) -> List[Dict]:
    data = json.loads(kb_path.read_text(encoding="utf-8"))
    products = data.get("products", [])
    if not isinstance(products, list):
        return []
    return products


def _fetch_existing(pharmacy_url: str) -> Dict[str, Dict]:
    resp = requests.get(f"{pharmacy_url}/products/", timeout=15)
    resp.raise_for_status()
    payload = resp.json()
    items = payload if isinstance(payload, list) else payload.get("results", [])
    existing_by_name: Dict[str, Dict] = {}
    for item in items:
        name = (item.get("name") or "").strip()
        if name:
            existing_by_name[name] = item
    return existing_by_name


def sync_catalog(kb_path: Path, pharmacy_url: str, update_existing: bool, deactivate_stale: bool) -> Dict[str, int]:
    products = _load_unified_products(kb_path)
    planned_payloads = [_to_payload(product) for product in products]
    existing_by_name = _fetch_existing(pharmacy_url)
    target_names = {payload["name"] for payload in planned_payloads if payload.get("name")}

    created = 0
    updated = 0
    skipped = 0
    failed = 0
    deactivated = 0

    for payload in planned_payloads:
        name = payload["name"]
        current = existing_by_name.get(name)

        try:
            if current is None:
                response = requests.post(f"{pharmacy_url}/products/", json=payload, timeout=20)
                if response.status_code in (200, 201):
                    created += 1
                else:
                    failed += 1
                    print(f"[FAIL][CREATE] {name} -> HTTP {response.status_code} :: {response.text[:180]}")
                continue

            if not update_existing:
                skipped += 1
                continue

            product_id = current.get("id")
            if product_id is None:
                failed += 1
                print(f"[FAIL][UPDATE] {name} -> missing id")
                continue

            response = requests.put(f"{pharmacy_url}/products/{product_id}/", json=payload, timeout=20)
            if response.status_code in (200, 202):
                updated += 1
            else:
                failed += 1
                print(f"[FAIL][UPDATE] {name} -> HTTP {response.status_code} :: {response.text[:180]}")

        except requests.RequestException as exc:
            failed += 1
            print(f"[ERROR] {name}: {exc}")

    if deactivate_stale:
        for existing_name, existing_item in existing_by_name.items():
            if existing_name in target_names:
                continue
            product_id = existing_item.get("id")
            if product_id is None:
                failed += 1
                print(f"[FAIL][DEACTIVATE] {existing_name} -> missing id")
                continue
            try:
                response = requests.patch(
                    f"{pharmacy_url}/products/{product_id}/",
                    json={"is_active": False},
                    timeout=20,
                )
                if response.status_code in (200, 202):
                    deactivated += 1
                else:
                    failed += 1
                    print(f"[FAIL][DEACTIVATE] {existing_name} -> HTTP {response.status_code} :: {response.text[:180]}")
            except requests.RequestException as exc:
                failed += 1
                print(f"[ERROR][DEACTIVATE] {existing_name}: {exc}")

    return {
        "target_products": len(products),
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "deactivated": deactivated,
        "failed": failed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync unified KB products into pharmacy-service catalog")
    parser.add_argument("--kb-path", default=str(DEFAULT_KB_PATH), help="Path to unified_kb.json")
    parser.add_argument("--pharmacy-url", default=DEFAULT_PHARMACY_URL, help="Pharmacy service base URL")
    parser.add_argument(
        "--no-update-existing",
        action="store_true",
        help="Only create missing products, do not update existing ones",
    )
    parser.add_argument(
        "--deactivate-stale",
        action="store_true",
        help="Set is_active=false for products not present in unified KB",
    )
    args = parser.parse_args()

    kb_path = Path(args.kb_path)
    if not kb_path.exists():
        raise SystemExit(f"KB file not found: {kb_path}")

    summary = sync_catalog(
        kb_path=kb_path,
        pharmacy_url=args.pharmacy_url.rstrip("/"),
        update_existing=not args.no_update_existing,
        deactivate_stale=args.deactivate_stale,
    )

    print("Sync completed")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
