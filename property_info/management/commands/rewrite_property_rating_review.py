# property_info/management/commands/rewrite_property_rating_review.py

import requests
import json
import re
from django.core.management.base import BaseCommand
from django.db import connections
from property_info.models import PropertyRatingReview

class Command(BaseCommand):
    help = "Generate property ratings and reviews, and save them to the database"

    def handle(self, *args, **options):
        with connections['travel'].cursor() as cursor:
            cursor.execute("""
                SELECT hotel_id, hotel_name, price, room_type, location, latitude, longitude 
                FROM hotels 
                LIMIT 2
            """)
            hotels = cursor.fetchall()

        for hotel_id, hotel_name, price, room_type, location, latitude, longitude in hotels:
            try:
                rating, review = self.generate_rating_and_review(hotel_name, price, room_type, location, latitude, longitude)

                if rating is None or review is None:
                    self.stdout.write(self.style.WARNING(f"Could not generate rating and review for hotel {hotel_name}. Saving fallback data."))
                    rating = 0.0  # Fallback rating
                    review = "Review not available"

                # Save the generated rating and review to the database
                PropertyRatingReview.objects.create(
                    property_id=hotel_id,
                    rating=rating,
                    review=review
                )

                self.stdout.write(self.style.SUCCESS(f"Rating and review for {hotel_name} saved."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing hotel {hotel_name}: {str(e)}"))

    def generate_rating_and_review(self, hotel_name, price, room_type, location, latitude, longitude):
        prompt = f"""Generate a rating (out of 5) and a review for the following hotel:

        Hotel Name: {hotel_name}
        Price: {price}
        Room Type: {room_type}
        Location: {location}
        Latitude: {latitude}
        Longitude: {longitude}

        The rating should be between 1 and 5, based on the overall hotel quality, amenities, and location. The review should provide insights into the hotel's key strengths and weaknesses within 3 lines."""

        try:
            response = requests.post(
                "http://ollama:11434/api/generate",  # URL for Ollama API
                json={
                    "model": "phi",
                    "prompt": prompt,
                    "system": "You are a hotel expert. Provide a rating and review in a concise format.",
                    "stream": False
                },
                timeout=None
            )

            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(f"Ollama API error: {response.text}"))
                return None, None

            response_data = response.json()
            if 'response' not in response_data:
                return None, None

            text = response_data['response']
            rating_match = re.search(r'Rating:\s*(\d+(\.\d+)?)', text)
            review_match = re.search(r'Review:\s*(.+)', text)

            if not rating_match or not review_match:
                self.stdout.write(self.style.WARNING(f"Could not parse response: {text}"))
                return None, None

            rating = float(rating_match.group(1))
            review = review_match.group(1).strip()

            return rating, review

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Request error: {str(e)}"))
            return None, None
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"JSON decode error: {str(e)}"))
            return None, None
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected error: {str(e)}"))
            return None, None




##########################################
# Run with:
# docker-compose exec django-new python manage.py rewrite_property_rating_review