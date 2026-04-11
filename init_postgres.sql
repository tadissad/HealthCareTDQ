-- init_postgres.sql
-- Khởi tạo các database riêng biệt cho từng microservice trong health-micro-ai
-- File này được chạy tự động khi PostgreSQL container khởi động lần đầu.

CREATE DATABASE patient_db;
CREATE DATABASE pharmacy_db;
CREATE DATABASE medical_catalog_db;
CREATE DATABASE prescription_db;
CREATE DATABASE dispensing_db;
CREATE DATABASE medical_review_db;
