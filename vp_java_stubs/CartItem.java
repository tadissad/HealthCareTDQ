import java.util.Date;
/** <<ORM Persistable>> prescription-service (cart-service) | db_table: cart_items */
public class CartItem {
    private int id;
    private int quantity;
    private Date added_at;
    private Date updated_at;
    private Customer customer;
    private MedicalProduct product;
}
