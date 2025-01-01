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
                WHERE hotel_id IS NOT NULL
                LIMIT 10
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
                existing_rating_review = PropertyRatingReview.objects.filter(property_id=hotel_id).first()

                if existing_rating_review:
                    # Update existing record
                    existing_rating_review.rating = rating
                    existing_rating_review.review = review
                    existing_rating_review.save()
                    self.stdout.write(self.style.SUCCESS(f"Updated rating and review for {hotel_name}"))
                else:
                    # Create new record
                    PropertyRatingReview.objects.create(
                        property_id=hotel_id,
                        rating=rating,
                        review=review
                    )
                    self.stdout.write(self.style.SUCCESS(f"Created new rating and review for {hotel_name}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing hotel {hotel_name}: {str(e)}"))

    def generate_rating_and_review(self, hotel_name, price, room_type, location, latitude, longitude):
        prompt = f"""Generate a rating (out of 5) and a review on the basis of what you are giving the rating for the following hotel:

        Hotel Name: {hotel_name}
        Price: {price}
        Room Type: {room_type}
        Location: {location}
        Latitude: {latitude}
        Longitude: {longitude}

        - If the rating is 1 or 2, the review should be negative, highlighting poor aspects such as bad service, poor amenities, or dissatisfaction with the experience.
        - If the rating is 3, the review should be neutral, pointing out both positive and negative aspects, indicating an average experience.
        - If the rating is 4 or 5, the review should be positive, praising the hotel for good service, excellent amenities, and a pleasant stay.

        Rating and review should be coherent and match the rating scale.

        The response format must be strictly as follows:
        Rating: <numeric value between 1 and 5>
        Review: <exactly 3 lines, no more than 100 words>
        """

        try:
            response = requests.post(
                "http://ollama:11434/api/generate",
                json={
                    "model": "phi",
                    "prompt": prompt,
                    "system": "You are a professional hotel reviewer. Provide concise, high-quality reviews in exactly 3 lines and no more than 100 words. Maintain a professional tone.",
                    "stream": False
                },
                timeout=None
            )

            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(f"Ollama API error: {response.text}"))
                return 0.0, "Review not available"

            response_data = response.json()
            if 'response' not in response_data:
                return 0.0, "Review not available"

            text = response_data['response']
            
            # Match variations like [RATING]: or Rating:
            rating_match = re.search(r'(?:\[RATING\]|Rating):\s*(\d+(\.\d+)?)', text, re.IGNORECASE)
            review_match = re.search(r'(?:[Review]|.*?):\s*(.+)', text, re.IGNORECASE)

            # Extract rating
            rating = float(rating_match.group(1)) if rating_match else 0.0

            # Extract review or fallback to remaining text
            review = text.split("\n", 1)[-1].strip() if not review_match else review_match.group(1).strip()
            review = review[:500]  # Truncate review if it's too long

            return rating, review

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Request error: {str(e)}"))
            return 0.0, "Review not available"
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"JSON decode error: {str(e)}"))
            return 0.0, "Review not available"
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected error: {str(e)}"))
            return 0.0, "Review not available"






##########################################
# Run with:
# docker-compose exec django-new python manage.py rewrite_property_rating_review