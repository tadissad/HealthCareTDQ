/** <<ORM Persistable>> dispensing-service | db_table: order_item */
public class OrderItem {
    private int id;
    private String name;
    private double price;
    private int quantity;
    private Order order;
    private MedicalProduct product;
}
