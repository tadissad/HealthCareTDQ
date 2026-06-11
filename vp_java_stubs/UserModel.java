import java.util.Date;
import java.util.List;
/** <<ORM Persistable>> auth-service | db_table: auth_users */
public class UserModel {
    private String user_id;
    private String email;
    private String password_hash;
    private boolean is_active;
    private boolean is_locked;
    private int failed_login_attempts;
    private Date last_login_at;
    private Date locked_until;
    private Date created_at;
    private Date updated_at;
    private List<TokenModel> tokens;
    private List<UserRoleModel> user_roles;
    private List<AuthLogModel> logs;
}
