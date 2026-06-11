/** <<ORM Persistable>> auth-service | db_table: auth_permissions */
public class PermissionModel {
    private int id;
    private String resource;
    private String action;
    private String description;
}
