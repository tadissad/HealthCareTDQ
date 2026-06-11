# 📚 Quick Setup Guide - Health-Micro-AI Category Update

## ⚡ TL;DR (30 giây)

```bash
# Chỉ cần chạy 1 lệnh duy nhất!
build.bat
```

Kết quả:
- ✅ 11 microservices khởi động
- ✅ 10 categories được tạo tự động
- ✅ 10 sản phẩm được seed vào DB
- ✅ Knowledge Graph (Neo4j) được khởi tạo
- ✅ Vector Store (FAISS) được khởi tạo

---

## 📊 10 Category Mới

| # | Category | Code | Icon | Sản Phẩm | Trạng Thái |
|----|---|---|---|---|---|
| 1 | Hỗ trợ Điều trị Viêm loét & HP | `ulcer_hp_support` | 🩹 | 3 | ✅ |
| 2 | Giảm Trào ngược & Ợ chua | `reflux_heartburn` | 🔥 | 3 | ✅ |
| 3 | Men vi sinh & Hỗ trợ Tiêu hóa | `probiotic_digestion` | 🦠 | 1 | ⚠️ |
| 4 | Tinh chất Nghệ & Thảo dược | `herbal_extract` | 🌿 | 0 | 🟡 |
| 5 | Thực phẩm & Dinh dưỡng Dạ dày | `stomach_nutrition` | 🥗 | 0 | 🟡 |
| 6 | Dụng cụ & Thiết bị Hỗ trợ | `equipment_device` | ⚙️ | 0 | 🟡 |
| 7 | Bộ xét nghiệm & Kiểm tra tại nhà | `test_kit_home` | 🧪 | 0 | 🟡 |
| 8 | Gói khám & Tư vấn Bác sĩ | `consultation_package` | 👨‍⚕️ | 0 | 🟡 |
| 9 | Dành cho Người già & Hệ tiêu hóa yếu | `elderly_weak_digestion` | 👴 | 3 | ✅ |
| 10 | Vitamin & Khoáng chất Bổ trợ | `vitamin_mineral` | 💊 | 0 | 🟡 |

---

## 📝 File Thay Đổi

| File | Thay Đổi | Status |
|------|----------|--------|
| `pharmacy-service/app/models.py` | Cập nhật CATEGORY_CHOICES (13 → 10) | ✅ |
| `seed_all.py` | Phân loại lại 10 sản phẩm + **PART D (new)** | ✅ |
| `build.bat` | Thêm bước seed categories | ✅ |

---

## 🚀 Chi Tiết Setup

### 1️⃣ Lần Đầu Chạy (Build AI + Compose + Seed)

```bash
cd health-micro-ai
build.bat
```

**Những gì xảy ra:**
```
[1/2] Build AI base image (PyTorch, FAISS, ...) ~15-40 min
[2/5] Docker Compose up -d (11 services)
[3/5] Django migrations (7 services)
[4/5] Seed categories (medical-catalog-service) ⭐ NEW
[5/5] Seed products + Neo4j + FAISS

➜ Website: http://localhost:8000
```

### 2️⃣ Lần Sau (Chỉ Seed Data)

```bash
python seed_all.py                # Seed tất cả
python seed_all.py --part A       # Chỉ products
python seed_all.py --part D       # Chỉ categories
```

### 3️⃣ Reset Dữ Liệu

```bash
# PostgreSQL
docker-compose exec -T pharmacy-service python manage.py flush --no-input
docker-compose exec -T medical-catalog-service python manage.py flush --no-input

# Rồi seed lại
python seed_all.py
```

---

## 🔄 Phân Loại Sản Phẩm (Mapping)

| Sản Phẩm | Cũ | → | Mới |
|---------|---|---|---|
| Phosphalugel | antacid | → | ulcer_hp_support |
| Nexium 20mg | ppi | → | reflux_heartburn |
| Omeprazole 20mg | ppi | → | reflux_heartburn |
| Ranitidine 150mg | h2_blocker | → | reflux_heartburn |
| Amoxicillin 500mg | antibiotic | → | ulcer_hp_support |
| Metronidazole 500mg | antibiotic | → | ulcer_hp_support |
| Lacidofil (Probiotic) | probiotic | → | probiotic_digestion |
| Smecta 3g | mucosal | → | elderly_weak_digestion |
| Domperidone 10mg | antiemetic | → | elderly_weak_digestion |
| Duspatalin 200mg | antispasmodic | → | elderly_weak_digestion |

---

## 🧪 Kiểm Tra

```bash
# Test 1: Check products
curl http://localhost:8002/products/ | jq '.[] | {name, category}'

# Expected:
# { "name": "Phosphalugel", "category": "ulcer_hp_support" }

# Test 2: Check categories
curl http://localhost:8003/categories/ | jq '.[] | {name, code}'

# Expected:
# { "name": "Hỗ trợ Điều trị Viêm loét & HP", "code": "ulcer_hp_support" }

# Test 3: Filter by category
curl "http://localhost:8002/products/?category=reflux_heartburn"
```

---

## 🎯 Chi Tiết 10 Category

### 🩹 Category 1: Hỗ trợ Điều trị Viêm loét & HP

**Subcategories:**
- Kháng sinh diệt H. pylori
- Bảo vệ niêm mạc & Chống acid

**Sản phẩm hiện tại:**
- Phosphalugel (gel kháng acid)
- Amoxicillin 500mg (kháng sinh)
- Metronidazole 500mg (kháng sinh)

---

### 🔥 Category 2: Giảm Trào ngược & Ợ chua

**Subcategories:**
- Ức chế bơm proton (PPI)
- Ức chế thụ thể H2

**Sản phẩm hiện tại:**
- Nexium 20mg (PPI)
- Omeprazole 20mg (PPI)
- Ranitidine 150mg (H2 Blocker)

---

### 🦠 Category 3: Men vi sinh & Hỗ trợ Tiêu hóa

**Subcategories:**
- Probiotics chứng chỉ y tế
- Hỗ trợ sau kháng sinh

**Sản phẩm hiện tại:**
- Lacidofil (Probiotic)

**Có thể mở rộng:**
- Optibac Probiotics
- BioGaia drops

---

### 🌿 Category 4: Tinh chất Nghệ & Thảo dược

**Subcategories:**
- Tinh chất Nghệ vàng
- Thảo dược kết hợp

**Sẵn sàng thêm:**
- Curcumin 500mg
- Ginger + Turmeric blend

---

### 🥗 Category 5: Thực phẩm & Dinh dưỡng Dạ dày

**Subcategories:**
- Sữa & Bột dinh dưỡng
- Thực phẩm hỗ trợ tiêu hóa

**Sẵn sàng thêm:**
- Sữa chuyên biệt cho dạ dày
- Cháo khô Hanu

---

### ⚙️ Category 6: Dụng cụ & Thiết bị Hỗ trợ

**Subcategories:**
- Thiết bị sưởi ấm
- Dụng cụ hỗ trợ uống thuốc

**Sẵn sàng thêm:**
- Túi nước ấm
- Dụng cụ nghiền viên

---

### 🧪 Category 7: Bộ xét nghiệm & Kiểm tra tại nhà

**Subcategories:**
- Test H. pylori tại nhà
- Kit xét nghiệm máu & nước tiểu

**Sẵn sàng thêm:**
- Urea Breath Test
- Blood glucose meter

---

### 👨‍⚕️ Category 8: Gói khám & Tư vấn Bác sĩ

**Subcategories:**
- Tư vấn trực tuyến
- Gói khám & theo dõi định kỳ

**Sẵn sàng thêm:**
- Video call 30 phút
- Gói 3 tháng follow-up

---

### 👴 Category 9: Dành cho Người già & Hệ tiêu hóa yếu

**Subcategories:**
- Thuốc chống nôn & điều hòa nhu động
- Thuốc chống co thắt & giảm đau bụng

**Sản phẩm hiện tại:**
- Domperidone 10mg (điều hòa nhu động)
- Duspatalin 200mg (chống co thắt)
- Smecta 3g (bảo vệ niêm mạc)

---

### 💊 Category 10: Vitamin & Khoáng chất Bổ trợ

**Subcategories:**
- Vitamin nhóm B & B12
- Khoáng chất: Mg, Zn, Ca

**Sẵn sàng thêm:**
- Vitamin B12 injection
- Magnesium supplement

---

## 📞 Troubleshooting

### ❌ Build Docker thất bại?

```bash
# Kiểm tra Docker
docker --version
docker ps

# Rebuild
docker system prune -f
build.bat rebuild
```

### ❌ Migration lỗi?

```bash
cd pharmacy-service
python manage.py migrate app zero      # Reset
python manage.py makemigrations
python manage.py migrate
```

### ❌ Seed script lỗi?

```bash
# Kiểm tra services đang chạy
docker-compose ps

# Xem log
docker-compose logs pharmacy-service
docker-compose logs medical-catalog-service

# Chạy lại
python seed_all.py --part D            # Chỉ categories
```

### ❌ API Gateway không route?

```bash
# Check gateway config
curl http://localhost:8000/api/products/
curl http://localhost:8000/api/categories/

# Nếu error, xem log
docker-compose logs api-gateway
```

---

## 🔗 API Endpoints

### Pharmacy Service (Products)

```bash
# Lấy tất cả products
GET http://localhost:8002/products/

# Filter by category
GET http://localhost:8002/products/?category=ulcer_hp_support

# Detail product
GET http://localhost:8002/products/1/

# Create product
POST http://localhost:8002/products/
```

### Medical Catalog Service (Categories)

```bash
# Lấy tất cả categories
GET http://localhost:8003/categories/

# Detail category
GET http://localhost:8003/categories/ulcer_hp_support/

# Get subcategories
GET http://localhost:8003/categories/ulcer_hp_support/subcategories/

# Get products in category
GET http://localhost:8003/categories/ulcer_hp_support/products/
```

### API Gateway (Route All)

```bash
# Route tới pharmacy-service
GET http://localhost:8000/api/products/

# Route tới medical-catalog-service
GET http://localhost:8000/api/categories/
```

---

## 🎉 Hoàn Tất!

✅ **10 categories** đã được tạo  
✅ **10 sản phẩm** đã được phân loại  
✅ **Tự động hóa** qua build.bat  
✅ **Sẵn sàng mở rộng** 7 categories còn lại  

Bắt đầu thêm sản phẩm vào các category trống hoặc tích hợp vào giao diện frontend!

---

**Version:** 1.0  
**Updated:** 20/04/2026  
**Status:** ✅ Ready to Deploy
