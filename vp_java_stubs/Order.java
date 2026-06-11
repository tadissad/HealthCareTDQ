import java.util.Date;
import java.util.List;
/** <<ORM Persistable>> dispensing-service | db_table: order */
public class Order {
    private int id;
    private String status; // Pending|Confirmed|Paid|Shipping|Delivered|Cancelled
    private String payment_method; // Cash|BankTransfer|MoMo|VNPAY|Insurance
    private String shipping_method; // Standard|Express|Pickup
    private String shipping_address;
    private double total_amount;
    private double discount_rate;
    private String note;
    private String prescription_code;
    private Date created_at;
    private Date updated_at;
    private Customer customer;
    private List<OrderItem> order_items;
}
