# Tổng Quan Hệ Thống: Health-Micro-AI

## 1. Kiến Trúc Tổng Thể

```
                          ┌─────────────────────────────────────────────┐
                          │              CLIENT (Browser)                │
                          └────────────────────┬────────────────────────┘
                                               │ HTTP :8000
                          ┌────────────────────▼────────────────────────┐
                          │              API GATEWAY                     │
                          │   Django – Port 8000 – SQLite (Account)     │
                          │   • Render HTML Templates (UI Layer)        │
                          │   • Proxy requests đến services             │
                          │   • Session Management (JWT in session)     │
                          └──┬──────┬──────┬──────┬──────┬──────┬──────┘
                             │      │      │      │      │      │
              ┌──────────────┼──────┼──────┼──────┼──────┼──────┼─────────────────┐
              │              │      │      │      │      │      │                 │
        ┌─────▼────┐   ┌─────▼───┐  │  ┌──▼────┐ │  ┌───▼────┐ │  ┌─────────────▼──┐
        │  auth-   │   │patient- │  │  │pharma-│ │  │medical-│ │  │prescriptn- │
        │ service  │   │ service │  │  │service│ │  │catalog │ │  │  service   │
        │:8012     │   │:8001    │  │  │:8002  │ │  │:8003   │ │  │:8004       │
        │FastAPI   │   │Django   │  │  │Django │ │  │Django  │ │  │FastAPI     │
        │JWT Token │   │Postgres │  │  │Postgr │ │  │Postgr  │ │  │Postgres    │
        └──────────┘   └─────────┘  │  └───────┘ │  └────────┘ │  └────────────┘
                                    │             │             │
                           ┌────────▼──┐  ┌───────▼──┐  ┌──────▼──────────────────┐
                           │dispensing-│  │medical-  │  │  clinical-advisory-   │
                           │ service   │  │ review-  │  │      service          │
                           │:8005      │  │ service  │  │:8013 FastAPI          │
                           │Django     │  │:8006     │  │ Neo4j + FAISS + Gemini│
                           │Postgres   │  │FastAPI   │  └───────────────────────┘
                           └───────────┘  │Postgres  │
                                          └──────────┘         ┌────────────────────┐
                                                               │treatment-recommender│
                                                               │     service        │
                                                               │:8011 FastAPI       │
                                                               │ Neo4j + GNN/SPD   │
                                                               └────────────────────┘
```

---

## 2. Danh Sách Services & Port Mapping

| Service | Tên Mới (Healthcare) | Port | Framework | Chức Năng |
|---|---|---|---|---|
| `api-gateway` | API Gateway | **8000** | Django | Cổng duy nhất, render UI, proxy |
| `auth-service` | Auth Service | **8012** | FastAPI | Quản lý JWT token |
| `patient-service` | Patient Service | **8001** | Django | Hồ sơ bệnh nhân, BHYT, membership |
| `pharmacy-service` | Pharmacy Service | **8002** | Django | Danh mục thuốc, tồn kho |
| `medical-catalog-service` | Medical Catalog Service | **8003** | Django | Phân loại thuốc, danh mục ICD-10 |
| `prescription-service` | Prescription Service | **8004** | FastAPI | Đơn thuốc tạm thời (basket) |
| `dispensing-service` | Dispensing Service | **8005** | Django | Phiếu xuất thuốc, thanh toán |
| `medical-review-service` | Medical Review Service | **8006** | FastAPI | Đánh giá hiệu quả điều trị |
| `treatment-recommender-service` | Treatment Recommender | **8011** | FastAPI | GNN + SPD Manifold recommendation |
| `clinical-advisory-service` | Clinical Advisory Service | **8013** | FastAPI | Chatbot GraphRAG (Neo4j+FAISS+Gemini) |

### Infrastructure

| Service | Port | Dùng Cho |
|---|---|---|
| **PostgreSQL** | 5432 | Lưu trữ dữ liệu quan hệ của tất cả Django services |
| **Neo4j** | 7474 (UI), 7687 (Bolt) | Knowledge Graph cho AI services |
| **Redis** | 6379 | Cache (sẵn sàng cho production) |

---

## 3. Nơi Lưu Trữ Dữ Liệu (Data Topology)

### A. PostgreSQL (Riêng biệt từng service)

```
PostgreSQL :5432
├── patient_db          ← patient-service
│   └── patients        (id, account_id, name, phone, email, address,
│                        blood_type, insurance_code, total_spent, membership)
│
├── pharmacy_db         ← pharmacy-service
│   └── products        (id, name, generic_name, category, dosage_form,
│                        dosage_strength, price, stock_quantity, requires_prescription,
│                        symptom_tags[], manufacturer, origin_country,
│                        description, side_effects, contraindications, usage_instruction)
│
├── medical_catalog_db  ← medical-catalog-service
│   └── categories      (id, name, slug, description, parent_id)
│
├── prescription_db     ← prescription-service
│   ├── cart_items      (id, customer_id, product_id, quantity, created_at)
│   └── [auto-cleared sau khi dispensing hoàn tất]
│
├── dispensing_db       ← dispensing-service
│   ├── orders          (id, customer_id, status, payment_method,
│                        shipping_method, discount_rate, total_amount,
│                        note, created_at)
│   └── order_items     (id, order_id, product_id, name, price, quantity)
│
└── medical_review_db   ← medical-review-service
    └── reviews         (id, product_id, customer_id, rating, comment,
                         treatment_effect, created_at)
```

### B. SQLite (api-gateway local)
```
api-gateway/db.sqlite3
└── accounts    (id, username, password[SHA-256], fullname, phone, email,
                 role, is_active, created_at)
```
> ⚠️ **Lưu ý**: Account và Customer Profile là **2 entity khác nhau** — Account quản lý đăng nhập, Patient quản lý thông tin y tế.

### C. Neo4j (Knowledge Graph – dùng chung cho 2 AI services)
```
Neo4j :7687
Nodes:
  ├── :User      {id, name}
  ├── :Product   {name, product_id}
  ├── :Disease   {name, icd10}
  ├── :Symptom   {name}
  ├── :Cause     {name}
  ├── :Diagnostic {name}
  └── :Category  {name}

Relationships:
  ├── (User)-[:SEARCHED {weight}]->(Symptom)
  ├── (User)-[:PURCHASED {quantity, date}]->(Product)
  ├── (User)-[:VIEWED {weight}]->(Product)
  ├── (Symptom)-[:INDICATES]->(Disease)
  ├── (Cause)-[:CAUSES]->(Disease)
  ├── (Disease)-[:TREATED_BY {priority}]->(Product)
  ├── (Disease)-[:DIAGNOSED_BY]->(Diagnostic)
  └── (Product)-[:BELONGS_TO]->(Category)
```

### D. FAISS Vector Store (clinical-advisory-service)
```
Volume: ai_faiss_data → /app/faiss_data/
├── medical.index       ← FAISS IndexFlatIP (cosine similarity, dim=384)
└── chunks.json         ← Danh sách text paragraphs tương ứng với mỗi vector
                           Nguồn: benhdaday.csv + faq.txt + manual paragraphs
                           ~32-45 chunks, mỗi chunk là 1 đoạn y văn
```

---

## 4. Luồng Dữ Liệu Chính (Data Flows)

### 4.1 Luồng Đăng Nhập (Auth Flow)
```
Browser → api-gateway (POST /login/)
    → [Local] Account.objects.get(username) → verify SHA-256 password
    → auth-service (POST /auth/login/) → trả JWT token
    → Lưu vào session: {account_id, username, fullname, role, jwt_token}
```

### 4.2 Luồng Mua Thuốc (End-to-End)
```
1. Xem danh sách thuốc
   api-gateway → pharmacy-service GET /products/
              → medical-review-service GET /reviews/summary/ (ratings)
              → treatment-recommender-service GET /api/recommend/ (AI)

2. Thêm vào đơn thuốc tạm thời
   api-gateway → prescription-service POST /cart-items/

3. Thanh toán (Checkout)
   api-gateway (POST /checkout/)
       → dispensing-service POST /orders/create/
           → prescription-service GET /carts/{id}/      (lấy items)
           → [Tạo Order + OrderItems trong dispensing_db]
           → [Áp dụng discount_rate nếu BHYT = 0.2]
           → prescription-service DELETE /carts/{id}/   (xóa đơn tạm)
           → patient-service PUT /patients/by-account/{id}/membership/ (cộng total_spent)
```

### 4.3 Luồng AI Chat (GraphRAG)
```
Browser → api-gateway POST /ai/chat/ (AJAX)
    → clinical-advisory-service POST /api/chat
        1. [Intent Detection] → phân loại: drug_info | symptom | diet | emergency
        2. [Neo4j Query] → tìm Symptom → Disease → Product (structured)
        3. [FAISS Search] → tìm text chunks liên quan (unstructured)
        4. [Gemini 1.5 Flash] → tổng hợp câu trả lời có medical disclaimer
        5. Trả về: {answer, intent_label, sources_count, mode}
```

### 4.4 Luồng AI Recommender (GNN + SPD Manifold)
```
Browser → api-gateway GET /ai/recommend/
    → treatment-recommender-service GET /api/recommend/?user_id=U{id}
        1. Lấy user interactions từ in-memory store (VIEWED, PURCHASED)
        2. SPDManifold.encode_user_behavior() → Covariance Matrix (SPD)
        3. GNN GraphSAGE embedding (từ Neo4j graph structure)
        4. HybridRecommender.recommend():
           score = α × GNN_cosine + (1-α) × AIRM_distance
        5. Top-K products → pharmacy-service GET /products/ (enrich info)
```

---

## 5. Luồng Xác Thực (JWT Internal)
```
api-gateway lưu JWT trong session → gắn vào header X-Internal-Token
khi gọi bất kỳ service nội bộ nào:
    headers = {'X-Internal-Token': jwt_token, 'Content-Type': 'application/json'}

auth-service ký JWT với JWT_SECRET (phải match giữa các services).
Các services nội bộ hiện tại KHÔNG verify JWT (trust internal network).
→ Production: cần thêm middleware verify JWT ở từng service.
```

---

## 6. ⚠️ Các Điểm Cần Chú Ý

### Bảo Mật
- **Password**: Đang dùng SHA-256 đơn giản. Production nên dùng `bcrypt` hoặc `argon2`.
- **No JWT Verification trên Internal Services**: Services nội bộ tin tưởng api-gateway. KHÔNG expose port của internal services ra ngoài internet.
- **CSRF**: Chỉ api-gateway có Django CSRF protection. Internal REST APIs không cần.
- **GEMINI_API_KEY**: Phải có trong `.env`, không commit lên git.

### Đặc Thù Healthcare
- **discount_rate (BHYT)**: Được gửi từ client qua hidden input, backend clamp trong `[0.0, 1.0]`. Hỗ trợ BHYT 80% → `discount_rate = 0.2`.
- **Thuốc kê đơn** (`requires_prescription = True`): Hệ thống hiển thị badge cảnh báo đỏ nhưng **chưa block mua**. Production cần thêm kiểm tra toa thuốc.
- **Medical Disclaimer**: Chatbot tự động append disclaimer vào mọi câu trả lời y tế.

### Dữ Liệu & AI
- **FAISS index** được persist vào Docker volume `ai_faiss_data`. Nếu xóa volume, cần chạy lại `seed_all.py --part C`.
- **Neo4j data** persist vào `neo4j_data`. Nếu xóa, cần chạy `seed_all.py --part B`.
- **Treatment Recommender** dùng in-memory store cho user interactions → **mất sau khi restart container**. Production: ghi vào Redis hoặc Neo4j.
- **Embedding Model** (`paraphrase-multilingual-MiniLM-L12-v2`) cache vào `ai_model_cache` volume. Download 1 lần ~500MB.

### Vận Hành
- **Boot order**: `postgres + neo4j` phải healthy trước. `ai-consulting-service` cần 60-120s để load model.
- **Database tự tạo**: `init_postgres.sql` tạo tất cả databases khi khởi tạo. Sau đó mỗi service Django chạy `migrate` tự động.
- **Seed data**: Phải chạy `python seed_all.py` sau khi tất cả services healthy.
- **Port conflicts**: Đảm bảo port 5432, 7474, 7687, 6379, 8000-8013 không bị chiếm.

---

## 7. Sơ Đồ Entity Relationship Cốt Lõi

```
Account (api-gateway) ─── 1:1 ──→ Patient (patient-service)
                                        │
                          1:N ──────────┘
                          │
                     Order (dispensing-service)
                          │ 1:N
                     OrderItem ──→ Product (pharmacy-service)
                                        │
                            1:N ────────┴──── 1:N
                            │                 │
                        Review           Symptom/Disease
                   (medical-review)        (Neo4j)
```
