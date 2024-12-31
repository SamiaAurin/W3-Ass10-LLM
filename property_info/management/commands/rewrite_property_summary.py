# this is property_info/management/commands/rewrite_property_summary.py
########################################


import requests
import json
from django.core.management.base import BaseCommand
from django.db import connections
from property_info.models import PropertySummary
from django.db.utils import IntegrityError

class Command(BaseCommand):
    help = "Generate property summary and save it to the database"

    def handle(self, *args, **options):
        with connections['travel'].cursor() as cursor:
            cursor.execute("""
                SELECT hotel_id, hotel_name, price, rating, room_type, location, latitude, longitude
                FROM hotels
                WHERE hotel_id IS NOT NULL
                LIMIT 10;
            """)
            hotels = cursor.fetchall()

        for hotel_id, hotel_name, price, rating, room_type, location, latitude, longitude in hotels:
            try:
                # Check if summary already exists
                existing_summary = PropertySummary.objects.filter(property_id=hotel_id).first()
                
                summary = self.generate_summary(hotel_name, price, rating, room_type, location, latitude, longitude)

                if summary is None:
                    self.stdout.write(self.style.WARNING(f"Could not generate summary for hotel ID {hotel_id}. Skipping."))
                    continue

                if existing_summary:
                    # Update existing record
                    existing_summary.summary = summary
                    existing_summary.save()
                    self.stdout.write(self.style.SUCCESS(f"Updated summary for {hotel_name}"))
                else:
                    # Create new record
                    PropertySummary.objects.create(
                        property_id=hotel_id,
                        summary=summary
                    )
                    self.stdout.write(self.style.SUCCESS(f"Created new summary for {hotel_name}"))

            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(f"Database integrity error for hotel ID {hotel_id}: {str(e)}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing hotel ID {hotel_id}: {str(e)}"))

    def generate_summary(self, hotel_name, price, rating, room_type, location, latitude, longitude):
        prompt = f"""Generate a summary for the following hotel:

        Hotel Name: {hotel_name}
        Price: {price}
        Rating: {rating}
        Room Type: {room_type}
        Location: {location}
        Latitude: {latitude}
        Longitude: {longitude}

        The summary should be concise, focusing on key details like location, amenities, and overall appeal."""

        try:
            response = requests.post(
                "http://ollama:11434/api/generate",
                json={
                    "model": "tinyllama",
                    "prompt": prompt,
                    "system": "You are a hotel expert. Respond in a concise, informative summary.",
                    "stream": False
                },
                timeout=None
            )

            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(f"Ollama API error: {response.text}"))
                return None

            response_data = response.json()
            if 'response' not in response_data:
                return None

            return response_data['response']

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Request error: {str(e)}"))
            return None
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"JSON decode error: {str(e)}"))
            return None
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected error: {str(e)}"))
            return None
##########################################
# Run with:
# docker-compose exec django-new python manage.py rewrite_property_summary