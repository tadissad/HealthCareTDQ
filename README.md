# Health-Micro-AI: Nền Tảng Y Tế Điện Tử Tích Hợp AI

Dự án **Health-Micro-AI** là một hệ thống e-commerce nhà thuốc điện tử dựa trên kiến trúc **Microservices** (10 services riêng biệt), kết hợp sức mạnh của Trí tuệ Nhân tạo (AI) trong việc **tư vấn y tế (GraphRAG)** và **gợi ý cá nhân hóa (GNN & SPD Manifold)**.

---

## 🌟 Tính Năng Nổi Bật

1. **Kiến Trúc Microservices**: 10 services hoạt động độc lập (Django & FastAPI), điều phối thông qua một API Gateway trung tâm. Cơ sở dữ liệu riêng biệt cho từng service.
2. **AI Tư Vấn Sức Khỏe (GraphRAG)**: 
   - Sử dụng **Neo4j** (Knowledge Graph) để biểu diễn mối quan hệ `Symptom - Disease - Product`.
   - Sử dụng **FAISS** (Vector Store) lưu trữ chuyên môn dạng text (FAQ, Cẩm nang ICD-10).
   - Tích hợp **Gemini 1.5 Flash** tổng hợp câu trả lời an toàn cho y tế.
3. **AI Gợi Ý Sản Phẩm (Recommendation)**:
   - Sử dụng Graph Neural Networks (GraphSAGE) kết hợp không gian SPD Manifold (Covariance Matrix) để khai phá hành vi người dùng, đưa ra gợi ý với độ chuẩn xác cao.
4. **Trải Nghiệm UI/UX Chuẩn Y Tế**:
   - Giao diện thiết kế theo Design System chuyên dụng (Light Theme, #1F6F5F Primary).
   - Tích hợp thanh toán **Bảo Hiểm Y Tế (BHYT)** tự động giảm trừ chi phí (80%).
   - Tracking các nhãn cảnh báo **"Thuốc Kê Đơn"**, Timeline theo dõi quá trình giao hàng chi tiết.

---

## 🏗️ Cấu Trúc Hệ Thống

```text
health-micro-ai/
├── api-gateway/                   # Django (Cổng giao tiếp UI & Internal Proxy)
├── auth-service/                  # FastAPI (Quản lý User, cấp phát JWT)
├── patient-service/               # Django (Quản lý thông tin bệnh nhân, BHYT)
├── pharmacy-service/              # Django (Quản lý nhà thuốc, sản phẩm y tế)
├── medical-catalog-service/       # Django (Danh mục chuyên môn: ICD-10, ATC)
├── prescription-service/          # FastAPI (Quản lý đơn thuốc tạm thời / basket)
├── dispensing-service/            # Django (Tạo phiếu xuất thuốc & thanh toán)
├── medical-review-service/        # FastAPI (Đánh giá chất lượng phác đồ / thuốc)
├── clinical-advisory-service/     # FastAPI (Chatbot GraphRAG: Neo4j + FAISS)
├── treatment-recommender-service/ # FastAPI (GNN + SPD Manifold Recommendation)
├── docker-compose.yml             # Cấu hình container cho Services, Postgres, Neo4j, Redis
└── seed_all.py                    # Script tạo dữ liệu mẫu và nạp tri thức y khoa AI
```

---

## 🚀 Hướng Dẫn Cài Đặt Và Chạy Hệ Thống

### Yêu cầu tiên quyết
- **Docker** và **Docker Compose**.
- Khởi tạo Python virtual environment (tuỳ chọn nếu chạy file seed).
- API Key của **Gemini** (Google AI Studio).

### Bước 1: Khởi Tạo Môi Trường Tùy Chỉnh (Environment variables)
Copy file `.env.example` thành `.env` ở thư mục gốc:
```bash
cp .env.example .env
```
Mở file `.env` vừa copy, cấu hình `GEMINI_API_KEY` của bạn để Chatbot AI hoạt động.

### Bước 2: Build Và Chạy Hệ Thống Với Docker
Giao việc thiết lập network, databases (Postgres, Neo4j, Redis), và services cho Docker Compose:
```bash
docker-compose up --build -d
```
Quá trình build lần đầu tiên sẽ mất thời gian một vài phút do cần phải cài đặt các thư viện AI đặc thù (`torch-geometric`, `sentence-transformers`, `faiss-cpu`...).

Kiểm tra trạng thái các container:
```bash
docker-compose ps
```

### Bước 3: Đổ Dữ Liệu Khởi Tạo (Seeding)
Sau khi toàn bộ các container báo trạng thái `UP` và webapp backend đã chạy (port 8000), bạn hãy chạy script seed để khởi tạo dữ liệu mẫu. (Lưu ý: Bạn cần cài đặt thư viện gốc trên máy `requests neo4j faiss-cpu sentence-transformers` nếu chạy ở máy host).

```bash
# Cài đặt thư viện trên môi trường venv của máy host (nếu có)
pip install requests neo4j faiss-cpu sentence-transformers numpy

# Chạy seed toàn bộ dữ liệu
python seed_all.py
```

*File `seed_all.py` tự động đọc thêm tri thức từ `benhdaday.csv` và `faq.txt`, giúp tạo ra Graph trên Neo4j và embeddings trên FAISS.*

### Bước 4: Trải Nghiệm Website
Truy cập vào trình duyệt:
👉 **http://localhost:8000** 

Dữ liệu User có sẵn (mật khẩu mặc định có thể tuỳ ý tạo trong lúc đăng ký, hoặc tạo Account mới trên Website):
- Tạo tài khoản mới, sau đó đăng nhập và mua một số sản phẩm để AI Recommender trên trang chủ bắt đầu "học bám theo" hành vi mua sắm của bạn.
- Nhấp chọn Thử AI Chat, đặt các câu hỏi xoay quanh bệnh dạ dày, hệ thống sẽ kết xuất file `faq.txt` và `benhdaday.csv`.

---

## 🛠️ Xử Lý Lỗi Thường Gặp (Troubleshooting)

1. **Lỗi `Cannot connect to Neo4j` khi đang seed:**
   Neo4j boot khá lâu nên đoạn script seed có thể kết nối trượt. Hãy đợi khoảng 30s sau khi `docker-compose up` rồi mới thực thi python script.
2. **Lỗi `Memory Error` khi compile torch-geometric:**
   Hạ thấp số threads của Docker Desktop, hoặc cấp thêm RAM trên setting UI của ứng dụng Docker (nên cấp trên 4GB RAM cho project này).
3. **Chatbot luôn báo "Không thể kết nối dịch vụ AI":**
   Kiểm tra container `clinical-advisory-service` qua command `docker-compose logs -f clinical-advisory-service`. Hãy chắc chắn rằng bạn cấu hình thẻ biến `GEMINI_API_KEY` đúng!

Chúc bạn thành công với Health-Micro-AI System!
