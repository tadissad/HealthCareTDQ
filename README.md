# Health-Micro-AI: Nền Tảng Y Tế Điện Tử Tích Hợp AI

Dự án **Health-Micro-AI** là một hệ thống e-commerce nhà thiết bị và sản phẩm y tế điện tử dựa trên kiến trúc **Microservices** (10 services riêng biệt), kết hợp sức mạnh của Trí tuệ Nhân tạo (AI) trong việc **tư vấn y tế (GraphRAG)** và **gợi ý cá nhân hóa (GNN & SPD Manifold)**. 

Đặc biệt, hệ thống đã được tối ưu hóa kiến trúc Cloud-Native, **gỡ bỏ hoàn toàn gánh nặng xử lý AI cục bộ (Local Model)** nặng hàng GB để trở nên cực kỳ nhẹ bén, phù hợp với mọi cấu hình Laptop cá nhân.

---

## 🌟 Tính Năng Nổi Bật

1. **Kiến Trúc Microservices Nhẹ Bén**: 10 services hoạt động độc lập (Django & FastAPI), điều phối thông qua một API Gateway trung tâm. CSDL tách biệt hoàn toàn.
2. **AI Tư Vấn Sức Khỏe (GraphRAG Cloud-Native)**: 
   - Thiết kế dựa trên **Neo4j** (Knowledge Graph) để biểu diễn rễ bệnh lý `Symptom - Disease - Product`.
   - Lưu trữ chuyên môn dạng text bằng **FAISS** (Vector Store) tối ưu tốc độ truy xuất.
   - Tích hợp **Gemini 2.0 Flash / Flash-Lite API** để phân tích tài liệu và tổng hợp câu trả lời chuẩn xác. Máy tính của bạn không tốn RAM để vắt sức chạy Mô hình ngôn ngữ lớn (LLM)!
3. **AI Gợi Ý Sản Phẩm (Recommendation)**:
   - Thuật toán Graph Neural Networks (GraphSAGE) kết hợp không gian SPD Manifold (Covariance Matrix) khai phá hành vi người tiêu dùng, gợi ý bám sát thực tế.
4. **Trải Nghiệm UI/UX Hệ Sinh Thái Y Tế**:
   - Giao diện thiết kế theo Design System chuyên dụng (Light Theme, #1F6F5F Primary).
   - Tích hợp thanh toán **Bảo Hiểm Y Tế (BHYT)** tự động giảm trừ chi phí (được hỗ trợ tới 80%).

---

## 🏗️ Cấu Trúc Hệ Thống Khuyên Dùng

```text
health-micro-ai/
├── api-gateway/                   # Django (Cổng giao tiếp UI & Internal Proxy)
├── auth-service/                  # FastAPI (Quản lý User, cấp phát JWT)
├── patient-service/               # Django (Quản lý thông tin bệnh nhân, Thẻ BHYT)
├── pharmacy-service/              # Django (Quản lý nhà thuốc, sản phẩm y tế gốc)
├── medical-catalog-service/       # Django (Kiểm tra Phác đồ chuyên môn: ICD-10, ATC)
├── prescription-service/          # FastAPI (Quản lý đơn thuốc tạm thời / Giỏ hàng)
├── dispensing-service/            # Django (Tạo phiếu xuất thuốc & Thanh toán hóa đơn)
├── medical-review-service/        # FastAPI (Đánh giá chất lượng trải nghiệm / Review)
├── clinical-advisory-service/     # FastAPI (Chatbot AI GraphRAG: Neo4j + FAISS + Gemini)
├── treatment-recommender-service/ # FastAPI (GNN + SPD Manifold Recommendation)
├── docker-compose.yml             # Cấu hình container cho 10 Services, Postgres, Neo4j
└── seed_all.py                    # Script quét tài liệu & Bơm dữ liệu mẫu tự động (Idempotent)
```

---

## 🚀 Hướng Dẫn Cài Đặt Và Chạy Hệ Thống

### 📋 Yêu Cầu Tiên Quyết
- Máy tính đã cài đặt **Docker Desktop** và **Docker Compose** (bật sẵn Docker Desktop trước khi chạy).
- Đã đăng ký API Key của **Gemini** (Lấy miễn phí tại Google AI Studio).
- Máy có cài đặt Python (Chỉ cần thiết nếu bạn muốn chạy lệnh nạp dữ liệu thủ công).

### Bước 1: Mở Khóa Phân Hệ Trí Tuệ Nhân Tạo (Bắt Buộc)
Mục tiêu: Cung cấp bộ não cho AI để nó có thể nói chuyện và suy luận.
Copy file `.env.example` thành `.env` ở thư mục gốc của dự án:
```bash
cp .env.example .env
```
Mở file `.env` vừa tạo, dán API Key của bạn vào biến:
`GEMINI_API_KEY=AIzaSyB-xxxxxxx_xxxxxxxxxxxxx`
*(Lưu ý: Thiếu bước này, AI sẽ không thể truy cập Cloud để xử lý ngôn ngữ và sẽ báo lỗi kết nối).*

### Bước 2: Build Và Khởi Động Toàn Diện (One-Click Deploy)
Hệ thống được trang bị "Kịch bản triển khai tự động" vô cùng tinh xảo. Để khởi động toàn bộ kiến trúc y tế phức tạp này từ con số 0, bạn **CHỈ CẦN GÕ MỘT LỆNH DUY NHẤT** tại Terminal (hoặc click đúp chuột):

```bat
.\build.bat
```
Ngay lập tức, kịch bản này sẽ vận hành quy trình chuẩn xác sau:
1. **Build AI Base Image:** Tạo nền tảng siêu nhẹ (~200MB) chứa các công cụ máy học AI cốt lõi vĩnh viễn (chỉ tốn khoảng 3-5 phút ở lần dùng máy tính đầu tiên).
2. **Kích hoạt Microservices:** Bật toàn bộ 13 container (Bao gồm Postgres, Neo4j, Gateway và 10 Web Services).
3. **Đồng bộ hóa CSDL (Auto-Migrate):** Tự động len lỏi vào 6 cụm máy chủ sử dụng nền tảng Django (`pharmacy`, `patient`, `dispensing`, `catalog`, `medical-review` và `api-gateway`) để thiết lập cấu trúc cho hàng chục Bảng dữ liệu liên kết. Không bao giờ còn lỗi "No such table".
4. **Bơm Kiến thức Chuyên Ngành (Auto-Seed):** Gọi script `seed_all.py` nạp hàng loạt Danh mục Thuốc, Bệnh lý vào đồ thị Neo4j và kho Vector FAISS. Cuối cùng tự đánh thức AI để cập nhật kiến thức.

**🔒 Cam Kết Tiêu Chuẩn Doanh Nghiệp:** 
- Xóa bỏ triệt để rủi ro Sập bộ nhớ (OS Error 1455) do loại bỏ hoàn toàn các Local Models nặng nề.
- Kiến trúc "Fault Tolerance": Ngay cả khi 1 vài service bị lỗi, Giao diện Web chính vẫn không bao giờ sập (Crash). 

### Bước 3: Nạp Dữ Liệu Nâng Cao (Tùy Chọn Hoàn Toàn)
Vì `build.bat` đã tự động xử lý mọi thứ, bạn có thể **BỎ QUA** bước này ở lần đầu sử dụng.
Tuy nhiên, nếu bạn muốn can thiệp dữ liệu sâu hơn (Sửa trong file `benhdaday.csv` hoặc bổ sung tri thức trong `faq.txt`) để gây ấn tượng trong buổi bảo vệ đồ án, hãy gọi lại thủ công lệnh sau:

```bash
# Đảm bảo cài đủ thư viện trên máy host:
pip install requests neo4j faiss-cpu google-genai numpy

# Chạy lệnh đào tạo dữ liệu mới:
python seed_all.py
```
*(Script này được thiết kế theo chuẩn Idempotent - Có thể chạy đè 100 lần mà không sợ rác dữ liệu).*

---

## 💻 Trải Nghiệm Thực Tế Hệ Sinh Thái

Khi `build.bat` hoàn tất (hiển thị màu xanh rực rỡ "HOÀN TẤT"), hãy truy cập bằng trình duyệt Chrome/Edge:
👉 **http://localhost:8000** 

1. **Đăng Ý / Đăng Nhập:** Khởi tạo tài khoản, JWT Token Auth Service sẽ được cấp phát ngay tắp lự.
2. **Mua Sắm Thiết Bị & Thuốc:** Thử trải nghiệm thanh toán giỏ hàng kết hợp với việc áp mã giảm trừ **Thẻ Bảo Hiểm Y Tế BHYT**.
3. **Tương tác với AI Chatbot (Neo4j + FAISS + Gemini):** 
   - Nhấn vào icon Tư Vấn AI và gõ câu: *"Tôi bị đau dạ dày phải làm sao?"*
   - ⚠️ **LƯU Ý CỰC KỲ QUAN TRỌNG VỀ ĐỘ TRỄ CHUẨN (LATENCY):** Ở ngay câu hỏi đầu tiên bạn nhắn cho AI, do hệ thống Node mạng phải Boot-up (Khởi động kết nối ra máy chủ Google Gemini, dịch nội dung Vector, truy quét Neo4j), thời gian xử lý có thể mất từ **15 đến 30 Giây**. Giao diện đã được tinh chỉnh để hiện Dấu ba chấm "..." và chờ đợi lên tới 90s thay vì gây Time-Out. Kể từ câu hỏi thứ 2 trở đi, mọi thứ sẽ diễn ra cực kỳ nhanh!

---

## 🛠️ Xử Lý Trục Trặc Bất Thường (Troubleshooting)

| Dấu hiệu Lỗi | Nguyên Nhân & Cách Xử Lý |
| --- | --- |
| Trang Chủ Trắng Xác / Crash Web | Do Docker chưa khởi chạy kịp hoặc Service Database bị đứng. Hãy mở Terminal, gõ `docker-compose restart api-gateway` |
| AI Chat báo lỗi "Không thể kết nối dịch vụ AI" hoặc chập chờn 503 | Cấu hình Timeout. Hãy chắc chắn bạn đã chạy lệnh `.\build.bat rebuild` nếu bạn từng chạy code cũ. Lỗi này đã được khắc phục hoàn toàn trong kiến trúc Timeout 60s mới nhất. |
| AI Chat luôn trả về cảnh báo "Thiếu API Key" | Kiểm tra ngay lại file `.env`. Nếu bạn sửa file khi container đang chạy, hãy gõ `docker-compose restart clinical-advisory-service` để Container nhận dạng mật khẩu mới. |
| Log báo lỗi **429 Too Many Requests** | Google Gemini giới hạn số câu hỏi miễn phí (15 RPM). AI của ta có Tích hợp *Model Fallback Chain* để tự rẽ nhánh sang model khác dự phòng. Để khắc phục triệt để, lấy 1 Email Google khác để lấy API Key mới dán vào là xong! |

---
*Kiến trúc Cloud-Native Tối Ưu Hóa Tuyệt Đối - Dành riêng cho Đồ án Y Tế Thông Minh*
