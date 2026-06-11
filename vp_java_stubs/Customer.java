import java.util.Date;
import java.util.List;
/** <<ORM Persistable>> patient-service | db_table: customer */
public class Customer {
    private int id;
    private int account_id;
    private String name;
    private String email;
    private String phone;
    private String address;
    private Date date_of_birth;
    private String blood_type; // A|B|O|AB với +/-
    private String insurance_code;
    private List medical_history; // JSONField
    private List allergies;       // JSONField
    private String membership;    // Bronze|Silver|Gold|Platinum
    private double total_spent;
    private Date created_at;
    private Date updated_at;
    private Account account;
}
