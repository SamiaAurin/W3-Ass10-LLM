# property_info/models.py


from django.db import models

class HotelNameDescription(models.Model):
    original_id = models.IntegerField()  # References the original hotel_id
    original_title = models.CharField(max_length=255)  # Original hotel name
    rewritten_title = models.CharField(max_length=255)  # Rewritten hotel name
    description = models.TextField()  # Generated description

    class Meta:
        db_table = 'HotelName_Description'  # The table name in your Ollama DB

    def __str__(self):
        return f"{self.original_title} -> {self.rewritten_title}"


class PropertySummary(models.Model):
    property_id = models.IntegerField(unique=True)  # Reference to the property
    summary = models.TextField()  # Summary generated by the LLM model

    class Meta:
        db_table = 'property_summary'

    def __str__(self):
        return f"Property ID: {self.property_id} - Summary"
        

class PropertyRatingReview(models.Model):
    property_id = models.IntegerField(unique=True)  # Reference to the property
    rating = models.FloatField()  # Rating generated by the LLM model
    review = models.TextField()  # Review generated by the LLM model

    class Meta:
        db_table = 'property_rating_review'

    def __str__(self):
        return f"Property ID: {self.property_id} - Rating: {self.rating}"