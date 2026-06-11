#  Hướng dẫn sử dụng Diagrams

Thư mục này chứa toàn bộ source code biểu đồ cho báo cáo **Health-Micro-AI**.

---

##  Danh sách file & Ảnh tương ứng

| File | Ảnh cần tạo | Công cụ | Ghi chú |
|---|---|---|---|
| `01_mono_vs_micro.md` | `mono_vs_micro.png` | **Mermaid** | So sánh Monolithic vs Microservices |
| `02_healthcare_monolithic.md` | `healthcare_monolithic.png` | **Mermaid** |  **THIẾU** - cần tạo mới |
| `03_healthcare_decomposition.md` | `healthcare_decomposition.png` | **Mermaid** | DDD 8 Bounded Contexts |
| `04_usecase_diagram.md` | `usecase_diagram.png` | **Mermaid** |  **THIẾU** - cần tạo mới |
| `05_microservice.md` | `microservice.png` | **Mermaid** | Kiến trúc tổng thể |
| `06_sequence_order.md` | `sequence_order.png` | **Mermaid** | Luồng mua thuốc |
| `07_activity_order.md` | `activity_order.png` | **Mermaid** | Quy trình thanh toán |
| `08_ai_architecture.md` | `ai_architecture.png` | **Mermaid** | AI Service pipeline |
| `09_class_auth_patient.puml` | `class_auth_patient.png` | **PlantUML** | Class: Auth + Patient |
| `10_class_pharmacy.puml` | `class_pharmacy.png` | **PlantUML** | Class: Pharmacy + Catalog |
| `11_class_prescription.puml` | `class_prescription.png` | **PlantUML** | Class: Prescription (Cart) |
| `12_class_dispensing.puml` | `class_dispensing.png` | **PlantUML** | Class: Dispensing (Order) |
| `13_classdiagram.puml` | `classdiagram.png` | **PlantUML** | Class tổng thể toàn hệ thống |
| `14_erd_dispensing.md` | `erd_dispensing.png` | **Mermaid** | ERD dispensing_db |
| `15_erd_pharmacy.md` | `erd_pharmacy.png` | **Mermaid** | ERD pharmacy_db |
| `16_erd_auth_patient.md` | `erd_auth_patient.png` | **Mermaid** | ERD auth + patient_db |

---

##  Cách xuất ảnh PNG

### Với file `.md` (Mermaid):
1. Mở file, **copy** đoạn code trong cặp ` ```mermaid ... ``` `
2. Truy cập **https://mermaid.live**
3. Paste vào phần **Code** bên trái
4. Bấm **Export** → **PNG**
5. Lưu file vào `../img/` với tên tương ứng trong bảng trên

### Với file `.puml` (PlantUML):
**Cách 1 — VSCode (đang dùng):**
- Mở file `.puml` → nhấn `Alt+D` để preview
- Click chuột phải vào preview → Export PNG

**Cách 2 — Online:**
1. Copy toàn bộ nội dung file `.puml`
2. Truy cập **https://www.plantuml.com/plantuml/uml**
3. Paste vào và tải về PNG

---

##  Trạng thái ảnh trong `../img/`

| Ảnh | Tình trạng |
|---|---|
| `mono_vs_micro.png` |  Thiếu — cần tạo từ `01_mono_vs_micro.md` |
| `healthcare_monolithic.png` |  Thiếu — cần tạo từ `02_healthcare_monolithic.md` |
| `usecase_diagram.png` |  Thiếu — cần tạo từ `04_usecase_diagram.md` |
| `healthcare_decomposition.png` |  Cần làm lại từ `03_healthcare_decomposition.md` |
| `microservice.png` |  Cần làm lại từ `05_microservice.md` |
| `sequence_order.png` |  Cần làm lại từ `06_sequence_order.md` |
| `activity_order.png` |  Cần làm lại từ `07_activity_order.md` |
| `ai_architecture.png` |  Cần làm lại từ `08_ai_architecture.md` |
| `class_auth_patient.png` |  Cần làm lại từ `09_class_auth_patient.puml` |
| `class_pharmacy.png` |  Cần làm lại từ `10_class_pharmacy.puml` |
| `class_prescription.png` |  Cần làm lại từ `11_class_prescription.puml` |
| `class_dispensing.png` |  Cần làm lại từ `12_class_dispensing.puml` |
| `classdiagram.png` |  Cần làm lại từ `13_classdiagram.puml` |
| `erd_dispensing.png` |  Cần làm lại từ `14_erd_dispensing.md` |
| `erd_pharmacy.png` |  Cần làm lại từ `15_erd_pharmacy.md` |
| `erd_auth_patient.png` |  Cần làm lại từ `16_erd_auth_patient.md` |
| `ai_chatbot.png` |  Giữ nguyên (screenshot thực tế) |
| `homepage.png` |  Giữ nguyên (screenshot thực tế) |
| `product_search.png` |  Giữ nguyên (screenshot thực tế) |
| `recommendations.png` |  Giữ nguyên (screenshot thực tế) |
| `prescription_management.png` |  Giữ nguyên (screenshot thực tế) |
| `thanhtoan.png` |  Giữ nguyên (screenshot thực tế) |
| `docker_logs.png` |  Giữ nguyên (screenshot thực tế) |
| `training_history.png` |  Giữ nguyên (chart thực tế AI) |
| `model_comparison.png` |  Giữ nguyên (chart thực tế AI) |
