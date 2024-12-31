import requests
import json
from django.core.management.base import BaseCommand
from django.db import connections
from property_info.models import HotelNameDescription

class Command(BaseCommand):
    help = "Change property titles and generate descriptions using Gemini model and save to ollama database"

    def handle(self, *args, **options):
        with connections['travel'].cursor() as cursor:
            cursor.execute("SELECT hotel_id, hotel_name, room_type, location FROM hotels LIMIT 2")
            hotels = cursor.fetchall()

        for hotel_id, hotel_name, room_type, location in hotels:
            try:
                hotel_name_new, description = self.rewrite_title_and_generate_description(hotel_name, room_type, location)

                # Handle fallback if parsing fails
                if hotel_name_new is None or description is None:
                    self.stdout.write(self.style.WARNING(f"Could not parse response for ID {hotel_id}. Saving fallback data."))
                    hotel_name_new = f"Could not parse the name"
                    description = "Description not available"

                # Create a new record
                HotelNameDescription.objects.create(
                    original_id=hotel_id,
                    original_title=hotel_name,
                    rewritten_title=hotel_name_new,
                    description=description
                )

                self.stdout.write(self.style.SUCCESS(
                    f"Original: {hotel_name}\nRewritten: {hotel_name_new}\nDescription: {description}\n"
                ))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing ID {hotel_id}: {str(e)}"))

    def rewrite_title_and_generate_description(self, title, room_type, location):
        prompt = f"""Change this hotel name and create a description following this exact format:
                    TITLE: [new hotel name]
                    DESCRIPTION: [hotel description]

                    Original hotel: {title}
                    Room type: {room_type}
                    Location: {location}"""

        try:
            # Add your API key to the request headers
            headers = {
                "Authorization": f"Bearer AIzaSyDUSM4OzooXQudrsXLMtqlGS73ZU_wtYsE",
                "Content-Type": "application/json"
            }

            response = requests.post(
                "https://aistudio.google.com/v1/models/gemini-2.0-flash-exp/predict",  # Replace with actual endpoint if needed
                headers=headers,  # Include the headers with the API key
                json={
                    "model": "gemini-2.0-flash-exp",
                    "prompt": prompt,
                    "system": "You are a hotel expert. Respond in the exact format specified.",
                    "stream": False
                },
                timeout=None
            )

            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(f"API error: {response.text}"))
                return f"Could not parse response: {response.text}", None

            response_data = response.json()
            if 'response' not in response_data:
                return f"Could not parse response: {response.text}", None

            text = response_data['response']

            # Use regex to extract TITLE and DESCRIPTION
            import re
            title_match = re.search(r'^TITLE:\s*(.+)', text, re.IGNORECASE | re.MULTILINE)
            description_match = re.search(r'^DESCRIPTION:\s*(.+)', text, re.IGNORECASE | re.MULTILINE)

            if not title_match or not description_match:
                self.stdout.write(self.style.WARNING(f"Could not parse response: {text}"))
                return f"Could not parse response: {text}", None

            new_title = title_match.group(1).strip()
            description = description_match.group(1).strip()

            if not new_title or not description:
                self.stdout.write(self.style.WARNING(f"Empty title or description in response: {text}"))
                return f"Could not parse response: {text}", None

            return new_title, description

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Request error: {str(e)}"))
            return f"Could not parse response: {str(e)}", None
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"JSON decode error: {str(e)}"))
            return f"Could not parse response: {str(e)}", None
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected error: {str(e)}"))
            return f"Could not parse response: {str(e)}", None
