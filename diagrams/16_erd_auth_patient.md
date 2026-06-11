
# Hình: erd_auth_patient
# ERD Data Model — auth (in-memory) + patient_db (SQLite Account)
# Dán code dưới vào https://mermaid.live để xuất ảnh PNG

```mermaid
erDiagram
    accounts {
        INT id PK
        VARCHAR username
        VARCHAR password
        VARCHAR fullname
        VARCHAR phone
        VARCHAR email
        VARCHAR role
        BOOLEAN is_active
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    patients {
        VARCHAR id PK
        VARCHAR account_id UK
        VARCHAR full_name
        VARCHAR email
        VARCHAR phone
        DATE date_of_birth
        VARCHAR gender
        VARCHAR blood_type
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    patient_addresses {
        INT id PK
        VARCHAR patient_id FK
        VARCHAR street
        VARCHAR ward
        VARCHAR district
        VARCHAR province
        VARCHAR postal_code
    }

    insurance_infos {
        INT id PK
        VARCHAR patient_id FK
        VARCHAR code
        FLOAT discount_rate
        DATE valid_until
    }

    medical_records {
        VARCHAR id PK
        VARCHAR patient_id FK
        DATE visit_date
        TEXT diagnosis
        TEXT notes
        TIMESTAMP created_at
    }

    accounts ||--|| patients :"account_id (logic FK)"patients ||--o| patient_addresses :"has address"patients ||--o| insurance_infos :"has insurance"patients ||--o{ medical_records :"has records"```
