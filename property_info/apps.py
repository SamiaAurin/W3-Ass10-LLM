
# property_info/apps.py
from django.apps import AppConfig

class PropertyInfoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'property_info'

    def ready(self):
        import property_info.admin  # Import the admin.py file