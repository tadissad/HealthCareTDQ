import java.util.Date;
/** <<ORM Persistable>> medical-review-service | db_table: review */
public class Review {
    private int id;
    private int rating;
    private String comment;
    private int effectiveness;
    private String side_effect_experience;
    private Date created_at;
    private MedicalProduct product;
    private Customer customer;
}