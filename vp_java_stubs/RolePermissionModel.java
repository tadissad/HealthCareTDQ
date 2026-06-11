import java.util.Date;
/** <<ORM Persistable>> auth-service | db_table: auth_role_permissions */
public class RolePermissionModel {
    private int id;
    private Date granted_at;
    private PermissionModel permission;
}
