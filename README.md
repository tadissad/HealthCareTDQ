# Health-Micro-AI: Nền Tảng Y Tế Điện Tử Tích Hợp AI

**Status**: ✅ **100% COMPLETE - 11 MICROSERVICES DEPLOYED**

Dự án **Health-Micro-AI** là một **hệ thống e-commerce y tế hoàn chỉnh** dựa trên kiến trúc **Microservices** (11 services độc lập), kết hợp sức mạnh của Trí tuệ Nhân tạo (AI) trong việc **tư vấn y tế (GraphRAG)** và **gợi ý cá nhân hóa (Collaborative Filtering)**. 

✅ **Đã hoàn thành**:
- 11 services microservices với 4-layer DDD architecture
- Event-driven communication qua RabbitMQ
- JWT authentication + Role-Based Access Control
- API Gateway với routing, rate limiting, health checks
- 50+ ORM models, 80+ HTTP endpoints, 65+ domain events
- ~38,000 dòng production-ready code
- Deployment ready (Docker Compose + manual setup)

Đặc biệt, hệ thống được tối ưu hóa kiến trúc Cloud-Native, **gỡ bỏ hoàn toàn gánh nặng xử lý AI cục bộ** để trở nên cực kỳ nhẹ bén.

---

## 🌟 Tính Năng Nổi Bật

### ✅ 1. Kiến Trúc Microservices Hoàn Chỉnh (11 Services)

| Service | Purpose | Layer | Technology |
|---------|---------|-------|-----------|
| **Patient Service** | Quản lý thông tin bệnh nhân, hồ sơ y tế | Django + DDD | PostgreSQL |
| **Pharmacy Service** | Quản lý dược phẩm, tồn kho, batch tracking | Django + DDD | PostgreSQL |
| **Prescription Service** | Quản lý đơn thuốc, giỏ hàng, fulfillment | Django + DDD | PostgreSQL |
| **Dispensing Service** | Phân phối thuốc, thanh toán, giao hàng | Django + DDD | PostgreSQL |
| **Medical-Catalog Service** | Tìm kiếm sản phẩm, phác đồ chuyên môn | Django + DDD | PostgreSQL |
| **Medical-Review Service** | Đánh giá cộng đồng, xếp hạng | Django + DDD | PostgreSQL |
| **Clinical-Advisory Service** | Chatbot AI (GraphRAG: Neo4j + FAISS + Gemini) | FastAPI + AI | Neo4j + FAISS |
| **Treatment-Recommender Service** | Gợi ý phác đồ (GNN + SPD Manifold) | FastAPI + ML | Neo4j |
| **Recommender-AI Service** | Gợi ý đơn giản (Collaborative Filtering) | Django + DDD | PostgreSQL |
| **Auth Service** | JWT auth, roles, permissions management | Django + DDD | PostgreSQL |
| **API Gateway** | Routing, rate limiting, health checks | FastAPI | - |

### ✅ 2. Kiến Trúc 4-Layer DDD (Consistent across all services)
```
┌─────────────────────────────────────────┐
│  Interface Layer (REST HTTP API)        │
├─────────────────────────────────────────┤
│  Application Layer (CQRS Commands)      │
├─────────────────────────────────────────┤
│  Domain Layer (Aggregates & Events)     │
├─────────────────────────────────────────┤
│  Infrastructure Layer (ORM & Repos)     │
└─────────────────────────────────────────┘
```

### ✅ 3. Event-Driven Architecture (RabbitMQ)
- **65+ Domain Events** cho inter-service communication
- **Async event publishing** từ tất cả services
- **Topic exchange** cho flexible routing
- **Loose coupling** giữa các services

### ✅ 4. Security Architecture
- **JWT Token Authentication** (HS256, access + refresh)
- **Role-Based Access Control (RBAC)** với permissions
- **API Gateway Rate Limiting** (per-service config)
- **Service-to-Service Authentication**
- **Account Locking** (failed login tracking)
- **Token Revocation & Blacklist**

### ✅ 5. AI Tích Hợp

#### Clinical-Advisory Service (GraphRAG)
- **Neo4j Knowledge Graph**: Symptom → Disease → Product relationships
- **FAISS Vector Store**: Medical documents retrieval
- **Gemini 2.0 Flash API**: Cloud-based LLM (no local models)
- **Evidence-based recommendations** từ medical knowledge

#### Treatment-Recommender Service (GNN)
- **Graph Neural Networks (GraphSAGE)**: User-product relationships
- **SPD Manifold**: Advanced ML recommendations
- **Personalized treatment suggestions**

#### Recommender-AI Service (Collaborative Filtering)
- **User-item interaction tracking**
- **Similarity-based recommendations**
- **Simplified but effective approach**

---

## 🏗️ Cấu Trúc Hệ Thống Chi Tiết

---

## 🚀 Hướng Dẫn Cài Đặt Và Chạy Hệ Thống

### 📋 Yêu Cầu Tiên Quyết
- **Docker Desktop** + **Docker Compose** (v3.8+)
- **Python 3.9+** (optional - chỉ cần nếu chạy seed data thủ công)
- **Gemini API Key** (miễn phí tại [Google AI Studio](https://aistudio.google.com))

### ⚡ Bước 1: Cấu Hình Biến Môi Trường

Copy `.env.example` → `.env`:
```bash
cp .env.example .env
```

Mở `.env` và thêm **Gemini API Key** (cần thiết cho Clinical-Advisory AI):
```env
GEMINI_API_KEY=AIzaSy...your_key_here...
JWT_SECRET=your-jwt-secret-key
```

### 🚀 Bước 2: Khởi Động Hệ Thống

**Windows (Recommended):**
```bat
.\build.bat
```

**Linux/Mac:**
```bash
bash build.sh
```

**Manual (Tất cả OS):**
```bash
docker-compose up -d
```

### ⏳ Bước 3: Chờ Services Khởi Động

```bash
# Kiểm tra trạng thái (chờ tất cả "Up")
docker-compose ps

# Xem logs (Ctrl+C để thoát)
docker-compose logs -f api-gateway

# Test API Gateway
curl http://localhost:8000/health
```

> ℹ️ **Lưu ý**: Lần đầu mất 2-4 phút. Services sau sẽ nhanh hơn.

### 🌐 Bước 4: Truy Cập Hệ Thống

| Service | URL | Mục Đích |
|---------|-----|---------|
| 🎯 **API Gateway** | http://localhost:8000 | Điểm vào chính |
| 🔐 **Auth Service** | http://localhost:8001 | Xác thực/phân quyền |
| 🏥 **Patient Service** | http://localhost:8002 | Quản lý bệnh nhân |
| 💊 **Pharmacy Service** | http://localhost:8003 | Quản lý kho dược |
| 📋 **Prescription Service** | http://localhost:8004 | Quản lý đơn thuốc |
| 🚚 **Dispensing Service** | http://localhost:8005 | Vận chuyển giao hàng |
| 🤖 **Clinical-Advisory (AI)** | http://localhost:8006 | Chatbot tư vấn y tế |
| 📊 **Medical-Catalog** | http://localhost:8007 | Tìm kiếm sản phẩm |
| ⭐ **Medical-Review** | http://localhost:8008 | Đánh giá cộng đồng |
| 🧠 **Recommender-AI** | http://localhost:8009 | Gợi ý cá nhân hóa |
| 🎮 **Treatment-Recommender (ML)** | http://localhost:8010 | Gợi ý phác đồ (GNN) |
| 📊 **Neo4j Database** | http://localhost:7474 | Knowledge Graph UI |
| 🐰 **RabbitMQ** | http://localhost:15672 | Message Queue (guest/guest) |

### 🌱 Bước 5: Nạp Dữ Liệu Mẫu (Tùy Chọn)

```bash
# Cài đặt thư viện cần thiết
pip install requests neo4j faiss-cpu google-generativeai numpy

# Chạy script nạp dữ liệu
python seed_all.py
```

---

## 💚 Trải Nghiệm Hệ Thống

Khi tất cả services khởi động xong, truy cập **http://localhost:8000** và thử:

### 1️⃣ Đăng Ký & Đăng Nhập
- Tạo tài khoản qua Auth Service
- Nhận JWT token (hợp lệ 24h)

### 2️⃣ Tìm Kiếm & Mua Sắm
- Search sản phẩm y tế
- Thêm vào giỏ
- Xem gợi ý cá nhân hóa
- Đọc đánh giá cộng đồng

### 3️⃣ 🤖 Tư Vấn AI (Clinical-Advisory)
Hỏi AI: *"Tôi bị đau dạ dày, mắt khoé bị chảy nước, sốt 39°C sáng sớm, phải làm sao?"*

**AI trả lời dựa trên:**
- Neo4j Knowledge Graph (symptom → disease → products)
- FAISS Vector Search (medical documents)
- Gemini 2.0 Flash (cloud LLM)

> ⏱️ **Lần đầu**: 15-30 giây. **Lần sau**: <1 giây

### 4️⃣ Xem Gợi Ý
- Collaborative Filtering (Recommender-AI)
- GNN + SPD Manifold (Treatment-Recommender) - nếu đã train

### 5️⃣ Quản Lý Đơn Thuốc
- Tạo prescription
- Track fulfillment
- Xem shipping status

---

## 🛠️ Troubleshooting

| Dấu hiệu Lỗi | Nguyên Nhân & Cách Xử Lý |
| --- | --- |
| Trang Chủ Trắng / 502 Bad Gateway | Docker chưa khởi động xong. Chạy `docker-compose logs api-gateway` |
| AI Chat báo "Connection Error" hoặc 503 | Chờ 1 phút (services đang boot). Hoặc chạy `docker-compose restart cli nical-advisory-service` |
| "Thiếu API Key" | Kiểm tra file `.env`, make sure `GEMINI_API_KEY` được set. Restart container: `docker-compose restart clinical-advisory-service` |
| "429 Too Many Requests" từ Gemini | Vượt giới hạn free tier (15 RPM). Lấy Email khác, API key mới, dán vào `.env` và restart |
| Database connection error | PostgreSQL chưa sẵn sàng. Chạy `docker-compose restart postgres` và chờ 10s |
| RabbitMQ events không được deliver | Chúc rabbitmq chạy: `docker-compose logs rabbitmq`. Kiểm tra binding queues trong RabbitMQ UI |

---
*Kiến trúc Cloud-Native Tối Ưu Hóa Tuyệt Đối - Dành riêng cho Đồ án Y Tế Thông Minh*
