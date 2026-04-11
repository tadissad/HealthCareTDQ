# ============================================================
# clinical-advisory-service/Dockerfile
# Kế thừa từ health-ai-base (PyTorch, FAISS, Transformers đã cài sẵn)
# Chỉ cần COPY code, mkdir FAISS dir và chạy.
# ============================================================

FROM health-ai-base:latest

WORKDIR /app

# Chỉ copy requirements để pip install PHẦN KHÁC BIỆT
# (tất cả AI libs đã có trong base ─ pip sẽ skip chúng ngay lập tức)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ source code
COPY . .

# Tạo thư mục lưu FAISS index
RUN mkdir -p /app/faiss_data

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
