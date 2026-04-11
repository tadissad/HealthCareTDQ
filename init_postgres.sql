-- init_postgres.sql
-- Khởi tạo các database riêng biệt cho từng microservice trong health-micro-ai
-- File này được chạy tự động khi PostgreSQL container khởi động lần đầu.

CREATE DATABASE customer_db;
CREATE DATABASE product_db;
CREATE DATABASE catalog_db;
CREATE DATABASE cart_db;
CREATE DATABASE order_db;
CREATE DATABASE comment_db;
