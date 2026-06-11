# Quan hệ giữa các Class — Thực tế dự án Health Micro AI (16 bảng)

Dưới đây là danh sách **đúng 16 class** thực tế đang được dùng trong code. Mỗi mục liệt kê chính xác class đó nối với gì, hình gì, bội số bao nhiêu.

## Ký hiệu (3 loại)
| Ký hiệu | Tên | Ý nghĩa |
|---|---|---|
| ◆── (diamond đen) | **Composition** | Con chết khi cha chết (Django `on_delete=CASCADE`) |
| ◇── (diamond trắng) | **Aggregation** | Con sống độc lập (Django `on_delete=SET_NULL`) |
| ──▶ (mũi tên thẳng) | **Association** | Tham chiếu mềm qua ID (cross-service, không có FK vật lý) |

---

### 1. Account
*Service: api-gateway*
- Vẽ **mũi tên thẳng (Association)** ──▶ tới **UserModel** (Bội số: 1 → 1) — Account gateway tương ứng với User trong auth-service
- *(Nhận mũi tên từ Customer)*

### 2. AuthLogModel
*Service: auth-service*
- *(Không kéo đi đâu. Nhận mũi tên Aggregation từ UserModel)*

### 3. CartItem
*Service: prescription-service (cart-service)*
- Vẽ **mũi tên thẳng (Association)** ──▶ tới **Customer** (Bội số: N → 1)
- Vẽ **mũi tên thẳng (Association)** ──▶ tới **MedicalProduct** (Bội số: N → 1)

### 4. Customer
*Service: patient-service*
- Vẽ **mũi tên thẳng (Association)** ──▶ tới **Account** (Bội số: 1 → 1) — soft ref qua account_id

### 5. MedicalCategory
*Service: medical-catalog-service*
- Vẽ **hình thoi đen (Composition)** ◆── ở MedicalCategory, mũi tên cắm vào **SubCategory** (Bội số: 1 → N)

### 6. MedicalProduct
*Service: pharmacy-service*
- *(Không kéo đi đâu. Nhận mũi tên từ CartItem, OrderItem, SubCategory, Review)*

### 7. Order
*Service: dispensing-service*
- Vẽ **hình thoi đen (Composition)** ◆── ở Order, mũi tên cắm vào **OrderItem** (Bội số: 1 → N)
- Vẽ **mũi tên thẳng (Association)** ──▶ tới **Customer** (Bội số: N → 1)

### 8. OrderItem
*Service: dispensing-service*
- Vẽ **mũi tên thẳng (Association)** ──▶ tới **MedicalProduct** (Bội số: N → 1)
- *(Cũng nhận mũi tên Composition từ Order)*

### 9. PermissionModel
*Service: auth-service*
- *(Không kéo đi đâu. Nhận mũi tên từ RolePermissionModel)*

### 10. Review
*Service: medical-review-service*
- Vẽ **mũi tên thẳng (Association)** ──▶ tới **MedicalProduct** (Bội số: N → 1)
- Vẽ **mũi tên thẳng (Association)** ──▶ tới **Customer** (Bội số: N → 1)

### 11. RoleModel
*Service: auth-service*
- Vẽ **hình thoi đen (Composition)** ◆── ở RoleModel, mũi tên cắm vào **RolePermissionModel** (Bội số: 1 → N)
- *(Cũng nhận mũi tên từ UserRoleModel)*

### 12. RolePermissionModel
*Service: auth-service*
- Vẽ **mũi tên thẳng (Association)** ──▶ tới **PermissionModel** (Bội số: N → 1)
- *(Cũng nhận mũi tên Composition từ RoleModel)*

### 13. SubCategory
*Service: medical-catalog-service*
- Vẽ **mũi tên thẳng (Association)** ──▶ tới **MedicalProduct** (Bội số: N → 1)
- *(Cũng nhận mũi tên Composition từ MedicalCategory)*

### 14. TokenModel
*Service: auth-service*
- *(Không kéo đi đâu. Nhận mũi tên Composition từ UserModel)*

### 15. UserModel
*Service: auth-service*
- Vẽ **hình thoi đen (Composition)** ◆── ở UserModel, mũi tên cắm vào **TokenModel** (Bội số: 1 → N)
- Vẽ **hình thoi đen (Composition)** ◆── ở UserModel, mũi tên cắm vào **UserRoleModel** (Bội số: 1 → N)
- Vẽ **hình thoi trắng (Aggregation)** ◇── ở UserModel, mũi tên cắm vào **AuthLogModel** (Bội số: 1 → N)

### 16. UserRoleModel
*Service: auth-service*
- Vẽ **mũi tên thẳng (Association)** ──▶ tới **RoleModel** (Bội số: N → 1)
- *(Cũng nhận mũi tên Composition từ UserModel)*

---

## Tổng hợp nhanh

```
[api-gateway]
Customer ──▶ Account          (1→1, soft ref)

[auth-service]
UserModel ◆──1→N── TokenModel
UserModel ◆──1→N── UserRoleModel ──▶ RoleModel
UserModel ◇──1→N── AuthLogModel
RoleModel ◆──1→N── RolePermissionModel ──▶ PermissionModel

[patient-service]
Customer ──▶ Account          (N→1, soft ref)

[medical-catalog-service]
MedicalCategory ◆──1→N── SubCategory ──▶ MedicalProduct

[prescription-service / cart-service]
CartItem ──▶ Customer         (N→1)
CartItem ──▶ MedicalProduct   (N→1)

[dispensing-service]
Order ◆──1→N── OrderItem ──▶ MedicalProduct
Order ──▶ Customer             (N→1)

[medical-review-service]
Review ──▶ MedicalProduct     (N→1)
Review ──▶ Customer            (N→1)
```
