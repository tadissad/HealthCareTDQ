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

### Yêu cầu tiên quyết
- Cài đặt **Docker** và **Docker Compose**.
- Đã đăng ký API Key của **Gemini** (Lấy miễn phí tại Google AI Studio).
- Máy tính có cài đặt Python (Nếu muốn chạy script nạp dữ liệu ở môi trường ngoài máy chủ).

### Bước 1: Khởi Tạo Môi Trường Tùy Chỉnh
Copy file `.env.example` thành `.env` ở thư mục gốc:
```bash
cp .env.example .env
```
Mở file `.env` vừa copy, dán mã `GEMINI_API_KEY` của bạn vào để "Mở khóa Trí Não" cho hệ thống AI. (Thiếu cái này AI sẽ bị căm, không trả lời được).

### Bước 2: Build Và Khởi Động Tự Động (One-Click Deploy)
Hệ thống đi kèm một "Kịch bản tự động thông minh" (Smart Script) giúp bạn bỏ qua mọi dòng lệnh quản trị rủi ro mạng. Bạn hoàn toàn có thể khởi động toàn bộ hệ thống từ con số 0 chỉ bằng MỘT LỆNH DUY NHẤT ở Terminal:

```bat
.\build.bat
```
Ngay khi chạy, tệp lệnh này sẽ làm thay bạn toàn bộ các công đoạn mệt mỏi:
1. Tạo một nền Base Image chia sẻ siêu nhẹ (~200MB) cực kỳ tiết kiệm bộ nhớ máy.
2. Kích hoạt bừng tỉnh 13 Containers của hệ thống y tế vi dịch vụ.
3. Tự động xâm nhập vào 6 cụm máy chủ Django để tạo cấu trúc Bảng Cố Lõi (Migrate).
4. Tự động nạp Dữ liệu Mẫu Thuốc và Kiến thức Bệnh học vào Trí Thông Minh Nhân Tạo (Seed AI).

**Cam kết:** Nhờ đập bỏ thiết kế Pytorch/SentenceTransformers cục bộ cũ, máy tính cá nhân của bạn sẽ KHÔNG bị Crash hay Tràn Bộ nhớ ảo (Lỗi OS Error 1455)!

Nếu bạn tò mò, hãy kiểm tra trạng thái các container đang xanh đèn bằng lệnh:
```bash
docker-compose ps
```

### Bước 3: Đổ Dữ Liệu Nâng Cao (Tùy Chọn - Manual Seeding)
Vì `build.bat` ở bước 2 đã tự động làm hết thay bạn, nên **bạn có thể BỎ QUA bước này** ở lần chạy đầu tiên.

Tuy nhiên, nếu sau này bạn **tự biên tập lại** cuốn bách khoa y khoa `faq.txt`, hay thêm các loại thuốc mới vào `benhdaday.csv` để đối phó với giảng viên, bạn có thể gọi thủ công lệnh dạy học này:

```bash
# Cài đặt thư viện vận chuyển trên máy chủ cá nhân của bạn
pip install requests neo4j faiss-cpu google-genai numpy

# Chạy công nhân xếp dữ liệu
python seed_all.py
```
*(Script có tính chất Idempotent - Chạy vô biên không trùng dữ liệu).*

> **Mẹo Nhỏ (Sau khi Seed tay xong):** Hãy gõ lệnh `docker-compose restart clinical-advisory-service` để đánh thức AI tái nạp lại bộ nhớ kiến thức mới nhất mà bạn vừa nạp!

### Bước 4: Trải Nghiệm Thực Tế Hệ Sinh Thái
Mọi cấu hình đã xong, hãy truy cập vào trình duyệt: 👉 **http://localhost:8000** 

- Khởi tạo 1 tài khoản mới theo ý thích. Trải nghiệm UI mua sắm, chọn mua vào Giỏ hàng và tiến hành **Thanh Toán (Checkout)** hóa đơn bảo hiểm y tế.
- Tương tác với tính năng "Gợi Ý Dành Riêng Cho Bạn" trên trang chủ, theo sát hành vi nhấp chuột của bạn.
- Nhấp chọn icon **Thử AI Chat**, gõ câu *"Tôi bị đau dạ dày, hãy cho tôi lời khuyên và danh mục thuốc chống viêm"*. Bot sẽ ngay lập tức đối chiếu chéo các CSDL với nhau để trả lời bạn bằng văn phong của một chuyên gia y khoa, kèm bằng chứng dẫn xuất từ chính cửa hàng của bạn!

---

## 🛠️ Xử Lý Lỗi Thường Gặp (Troubleshooting)

1. **Lỗi `Cannot connect to Neo4j` khi đang gõ lệnh seed:**
   Môi trường máy tính của bạn có thể boot hệ quản trị Graph Neo4j hơi tốn thời gian (khoảng 20-30 giây). Khắc phục: chờ cho 13 Container ở trạng thái Healthy hoàn toàn rồi mới hãy gõ lệnh `python seed_all.py`.
   
2. **Chatbot luôn báo "Không thể kết nối dịch vụ AI" hoặc bị đơ Template:**
   Nguyên nhân là thư mục Vector `faiss_seed_output/medical.index` chưa được lưu hoặc đọc đúng cách, HOẶC bạn quên mất nhập Key vào file `.env`. 
   Khắc phục: Dán Key vào biến `GEMINI_API_KEY` và gõ lệnh khởi động lại Service Cố Vấn: `docker-compose restart clinical-advisory-service`.

3. **Log bào lỗi `429 Too Many Requests` (Hết lượt gọi API của Google):**
   Đừng lo lắng! AI của Health-Micro có thiết lập **Trình chống nghẽn (Model Fallback Chain)** tự động trượt qua nhiều bậc não nhỏ khác nhau của Google nếu model `gemini-2.0-flash` ưu tiên cạn kiệt. Nếu xui rủi tất cả model đều bị sập do bạn quá lạm dụng gói Free, chỉ việc lấy email Mới đăng ký thêm 1 API Key vứt vào File Env là nó lại chạy phà phà!

---
*Phát triển và hoàn thiện dành riêng cho Hệ thống Y tế.*
