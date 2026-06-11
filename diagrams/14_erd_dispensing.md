
# Hình: erd_dispensing
# ERD Data Model — dispensing_db
# Dán code dưới vào https://mermaid.live để xuất ảnh PNG

```mermaid
erDiagram
    orders {
        UUID id PK
        VARCHAR customer_id
        VARCHAR prescription_id
        VARCHAR status
        NUMERIC subtotal
        NUMERIC discount_amount
        NUMERIC total_amount
        VARCHAR currency
        TIMESTAMP order_date
        TIMESTAMP confirmed_date
        TIMESTAMP dispensed_date
        TEXT notes
    }

    order_items {
        VARCHAR id PK
        UUID order_id FK
        VARCHAR product_id
        VARCHAR sku
        VARCHAR product_name
        INT qty_ordered
        INT qty_dispensed
        VARCHAR qty_unit
        NUMERIC unit_price
        NUMERIC line_total
        VARCHAR currency
    }

    payments {
        INT id PK
        UUID order_id FK
        VARCHAR method
        VARCHAR status
        VARCHAR transaction_id
        VARCHAR reference_number
        TIMESTAMP paid_at
    }

    shipping_infos {
        INT id PK
        UUID order_id FK
        VARCHAR street
        VARCHAR city
        VARCHAR district
        VARCHAR postal_code
        VARCHAR country
        TEXT notes
    }

    orders ||--o{ order_items :"contains"orders ||--o| payments :"has payment"orders ||--o| shipping_infos :"has shipping"```
