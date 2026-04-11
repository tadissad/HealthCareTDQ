FROM python:3.11-slim

WORKDIR /app

# Cài đặt dependencies hệ thống cần thiết cho PyTorch Geometric
RUN apt-get update && apt-get install -y \
    gcc g++ build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# 1. Cài PyTorch CPU trước (không cần CUDA)
RUN pip install --no-cache-dir torch==2.2.0 --index-url https://download.pytorch.org/whl/cpu

# 2. Cài torch-geometric và các extensions
RUN pip install --no-cache-dir torch-geometric

# 3. Cài phần còn lại
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
