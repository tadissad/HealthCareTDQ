import java.util.Date;
/** <<ORM Persistable>> auth-service | db_table: auth_user_roles */
public class UserRoleModel {
    private int id;
    private String role;
    private Date assigned_at;
    private String assigned_by;
    private RoleModel roleModel;
}
