# Quick API Test Guide

Hướng dẫn test nhanh các API endpoints sau khi deployment.

## 1️⃣ Health Check

### Test API Gateway Hoạt Động
```bash
curl http://localhost:8000/health
```

**Expected Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "auth": "healthy",
    "patient": "healthy",
    "pharmacy": "healthy"
  }
}
```

---

## 2️⃣ Auth Service (Đăng Ký & Đăng Nhập)

### Register New User
```bash
curl -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "name": "John Doe"
  }'
```

**Expected Response (201):**
```json
{
  "user_id": "user_123",
  "email": "user@example.com",
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 86400
}
```

### Login
```bash
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

### Save Token for Later Use
```bash
export TOKEN="eyJhbGciOiJIUzI1NiIs..."  # Paste from login response
```

---

## 3️⃣ Patient Service

### Create Patient
```bash
curl -X POST http://localhost:8002/api/patients \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Nguyễn Văn A",
    "date_of_birth": "1990-05-15",
    "phone": "0901234567",
    "address": "123 Đường ABC, TP HCM"
  }'
```

### Get Patient Info
```bash
curl http://localhost:8002/api/patients/patient_123 \
  -H "Authorization: Bearer $TOKEN"
```

---

## 4️⃣ Pharmacy Service

### Search Products
```bash
curl "http://localhost:8003/api/products/search?query=thuoc+ho" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Product Details
```bash
curl http://localhost:8003/api/products/product_456 \
  -H "Authorization: Bearer $TOKEN"
```

---

## 5️⃣ Prescription Service

### Create Prescription
```bash
curl -X POST http://localhost:8004/api/prescriptions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient_123",
    "prescriber_id": "doctor_456",
    "items": [
      {
        "product_id": "product_789",
        "quantity": 2,
        "dosage": "1 viên x 3 ngày"
      }
    ]
  }'
```

### Add Item to Prescription
```bash
curl -X POST http://localhost:8004/api/prescriptions/rx_001/items \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "product_101",
    "quantity": 1,
    "dosage": "2 viên x 2 ngày"
  }'
```

### Submit Prescription
```bash
curl -X PUT http://localhost:8004/api/prescriptions/rx_001/submit \
  -H "Authorization: Bearer $TOKEN"
```

---

## 6️⃣ 🤖 Clinical-Advisory (AI Chatbot)

### Ask AI Questions
```bash
curl -X POST http://localhost:8006/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Tôi bị đau dạ dày kéo dài, phải làm sao?",
    "session_id": "session_123"
  }'
```

**Expected Response:**
```json
{
  "answer": "Đau dạ dày có thể do nhiều nguyên nhân...",
  "sources": [
    {
      "document": "Medical Knowledge Base",
      "relevance": 0.95
    }
  ],
  "products_recommended": [
    {
      "product_id": "med_001",
      "name": "Thuốc kháng acid",
      "confidence": 0.88
    }
  ],
  "processing_time_ms": 2340
}
```

### Debug AI Intent Detection
```bash
curl -X POST http://localhost:8006/api/debug/intent \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Có triệu chứng nào của bệnh tiểu đường không?"
  }'
```

---

## 7️⃣ Recommender-AI Service

### Get Recommendations for User
```bash
curl "http://localhost:8009/api/recommendations?user_id=user_123&limit=5" \
  -H "Authorization: Bearer $TOKEN"
```

### Generate Fresh Recommendations
```bash
curl -X POST http://localhost:8009/api/recommendations/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "recommendation_type": "based_on_viewing_history"
  }'
```

---

## 8️⃣ Medical-Catalog Service

### Search by Category
```bash
curl "http://localhost:8007/api/products?category=Dung+cu+y+te&price_max=500000" \
  -H "Authorization: Bearer $TOKEN"
```

### List All Categories
```bash
curl http://localhost:8007/api/categories \
  -H "Authorization: Bearer $TOKEN"
```

---

## 9️⃣ Medical-Review Service

### Add Review for Product
```bash
curl -X POST http://localhost:8008/api/reviews \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "product_789",
    "user_id": "user_123",
    "rating": 5,
    "title": "Sản phẩm tuyệt vời",
    "content": "Chất lượng tốt, giao nhanh",
    "verified_purchase": true
  }'
```

### Get Product Reviews
```bash
curl "http://localhost:8008/api/products/product_789/reviews" \
  -H "Authorization: Bearer $TOKEN"
```

### Upvote Helpful Review
```bash
curl -X POST http://localhost:8008/api/reviews/review_123/upvote \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔟 Common HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | ✅ API call thành công |
| 201 | Created | ✅ Resource được tạo |
| 400 | Bad Request | ❌ Kiểm tra lại request body |
| 401 | Unauthorized | ❌ Token không hợp lệ, đăng nhập lại |
| 403 | Forbidden | ❌ Không có quyền truy cập |
| 404 | Not Found | ❌ Resource không tồn tại |
| 429 | Too Many Requests | ⏸️ Vượt giới hạn API, chờ 1 phút |
| 500 | Server Error | 🔧 Service lỗi, kiểm tra logs |
| 503 | Service Unavailable | 🔧 Service chưa sẵn sàng |

---

## 📊 Debugging Tips

### Check Service Logs
```bash
# Xem logs của một service cụ thể
docker-compose logs -f clinical-advisory-service

# Xem logs của tất cả services
docker-compose logs -f

# Xem logs của 50 dòng cuối cùng
docker-compose logs --tail=50
```

### Restart Services
```bash
# Restart một service
docker-compose restart auth-service

# Restart tất cả
docker-compose restart
```

### View Running Containers
```bash
docker-compose ps
```

### Access Database Directly
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres

# List databases
\l

# Connect to specific db
\c health_micro_db

# View tables
\dt
```

### RabbitMQ Management UI
- URL: http://localhost:15672
- Username: guest
- Password: guest

### Neo4j Browser
- URL: http://localhost:7474
- Query example: `MATCH (n:Symptom) RETURN n LIMIT 10`

---

## 📝 Notes

- **Token Expiry**: JWT tokens hợp lệ 24 giờ
- **Rate Limiting**: API Gateway giới hạn 100 requests/phút per service
- **Event Processing**: Domain events được publish async qua RabbitMQ (không chờ response)
- **AI Latency**: Lần đầu hỏi AI mất 15-30s (cold start), lần sau <1s

---

