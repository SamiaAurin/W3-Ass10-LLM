from django.contrib import admin
from .models import Hotel, PropertySummary, PropertyRatingReview

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ('hotel_id', 'hotel_name', 'price', 'rating', 'room_type', 'location', 'description')
    #search_fields = ('hotel_name', 'location', 'room_type')
    #list_filter = ('rating', 'price')
    
    def get_queryset(self, request):
        # Override queryset to fetch data from the 'travel' database
        return super().get_queryset(request).using('travel')

    def save_model(self, request, obj, form, change):
        # Ensure saving to the 'travel' database
        obj.save(using='travel')

@admin.register(PropertySummary)
class PropertySummaryAdmin(admin.ModelAdmin):
    list_display = ('property_id', 'summary')
    search_fields = ('property_id',)

@admin.register(PropertyRatingReview)
class PropertyRatingReviewAdmin(admin.ModelAdmin):
    list_display = ('property_id', 'rating', 'review')
    search_fields = ('property_id',)