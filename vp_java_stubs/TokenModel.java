import java.util.Date;
/** <<ORM Persistable>> auth-service | db_table: auth_tokens */
public class TokenModel {
    private int id;
    private String token_hash;
    private String token_type;
    private Date expires_at;
    private Date revoked_at;
    private Date created_at;
}
