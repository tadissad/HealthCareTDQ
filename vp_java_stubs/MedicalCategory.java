import java.util.Date;
import java.util.List;
/** <<ORM Persistable>> medical-catalog-service | db_table: medical_categories */
public class MedicalCategory {
    private int id;
    private String name;
    private String code;
    private String description;
    private String icon;
    private boolean is_active;
    private Date created_at;
    private List<SubCategory> subcategories;
}
