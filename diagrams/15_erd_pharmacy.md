
# Hình: erd_pharmacy
# ERD Data Model — pharmacy_db
# Dán code dưới vào https://mermaid.live để xuất ảnh PNG

```mermaid
erDiagram
    products {
        VARCHAR id PK
        VARCHAR sku
        VARCHAR generic_name
        VARCHAR trade_name
        VARCHAR category
        VARCHAR dosage_form
        VARCHAR dosage_strength
        VARCHAR atc_code
        BOOLEAN requires_prescription
        NUMERIC price_amount
        VARCHAR price_currency
        INT total_quantity
        INT min_stock_level
        INT reorder_point
        BOOLEAN active
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    manufacturers {
        INT id PK
        VARCHAR product_id FK
        VARCHAR name
        VARCHAR country
        VARCHAR registration_code
    }

    batches {
        VARCHAR id PK
        VARCHAR product_id FK
        VARCHAR batch_number
        INT quantity
        VARCHAR quantity_unit
        DATE expiry_date
        DATE received_date
    }

    inventory_locations {
        VARCHAR id PK
        VARCHAR product_id FK
        VARCHAR warehouse
        VARCHAR shelf
        VARCHAR row
        VARCHAR column
    }

    products ||--o| manufacturers :"has"products ||--o{ batches :"has batches"products ||--o{ inventory_locations :"stored at"```
