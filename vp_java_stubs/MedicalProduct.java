import java.util.Date;
import java.util.List;
/** <<ORM Persistable>> pharmacy-service | db_table: medical_product */
public class MedicalProduct {
    private int id;
    private String name;
    private String generic_name;
    private String category;
    private String dosage_form;
    private String dosage_strength;
    private String manufacturer;
    private String origin_country;
    private double price;
    private String unit;
    private int stock_quantity;
    private String description;
    private String side_effects;
    private String contraindications;
    private String usage_instruction;
    private boolean requires_prescription;
    private List symptom_tags; // JSONField
    private boolean is_active;
    private Date created_at;
    private Date updated_at;
}
