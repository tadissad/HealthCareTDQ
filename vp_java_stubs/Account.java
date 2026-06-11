import java.util.Date;
/** <<ORM Persistable>> api-gateway | db_table: account */
public class Account {
    private int id;
    private String username;
    private String password;
    private String fullname;
    private String phone;
    private String email;
    private String address;
    private String role; // customer | manager | staff | admin
    private boolean is_active;
    private Date created_at;
    private Date updated_at;
    private UserModel user;
}

