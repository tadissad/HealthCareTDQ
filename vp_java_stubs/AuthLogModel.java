import java.util.Date;
/** <<ORM Persistable>> auth-service | db_table: auth_logs */
public class AuthLogModel {
    private int id;
    private String event_type;
    private String email;
    private String ip_address;
    private Object details; // JSONB
    private Date occurred_at;
}
