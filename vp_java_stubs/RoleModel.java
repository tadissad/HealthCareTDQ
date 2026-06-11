import java.util.Date;
import java.util.List;
/** <<ORM Persistable>> auth-service | db_table: auth_roles */
public class RoleModel {
    private int id;
    private String name;
    private String description;
    private Date created_at;
    private List<RolePermissionModel> permissions;
}
