from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class CategoryDefinition:
    code: str
    name: str
    description: str


CATEGORIES: List[str] = [
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
]

CATEGORY_DEFINITIONS: List[CategoryDefinition] = [
    CategoryDefinition("ulcer_hp_support", "Hỗ trợ viêm loét & H. pylori", "Nhóm sản phẩm hỗ trợ điều trị viêm loét dạ dày và H. pylori."),
    CategoryDefinition("reflux_heartburn", "Giảm trào ngược & ợ chua", "Nhóm sản phẩm giảm acid và cải thiện triệu chứng trào ngược."),
    CategoryDefinition("probiotic_digestion", "Probiotic tiêu hóa", "Nhóm sản phẩm hỗ trợ cân bằng hệ vi sinh đường ruột."),
    CategoryDefinition("herbal_extract", "Chiết xuất thảo dược", "Nhóm sản phẩm nguồn gốc thảo dược cho tiêu hóa."),
    CategoryDefinition("stomach_nutrition", "Dinh dưỡng dạ dày", "Nhóm sản phẩm hỗ trợ dinh dưỡng cho hệ tiêu hóa."),
    CategoryDefinition("equipment_device", "Thiết bị y tế", "Nhóm thiết bị hỗ trợ theo dõi và chăm sóc sức khỏe."),
    CategoryDefinition("test_kit_home", "Bộ test tại nhà", "Nhóm bộ test nhanh và xét nghiệm tại nhà."),
    CategoryDefinition("consultation_package", "Gói khám & tư vấn", "Nhóm dịch vụ tư vấn và gói khám y tế."),
    CategoryDefinition("elderly_weak_digestion", "Người cao tuổi & tiêu hóa yếu", "Nhóm hỗ trợ người lớn tuổi hoặc hệ tiêu hóa yếu."),
    CategoryDefinition("vitamin_mineral", "Vitamin & khoáng chất", "Nhóm bổ sung vitamin và khoáng chất."),
]
