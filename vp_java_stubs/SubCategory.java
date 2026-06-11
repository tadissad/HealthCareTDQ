import java.util.Date;
import java.util.List;
/** <<ORM Persistable>> medical-catalog-service | db_table: sub_categories */
public class SubCategory {
    private int id;
    private String name;
    private String code;
    private String description;
    private boolean is_active;
    private Date created_at;
    private List<MedicalProduct> products;
}
