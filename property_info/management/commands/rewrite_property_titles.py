# this is property_info/management/commands/rewrite_property_titles.py
########################################

import requests
import json
from django.core.management.base import BaseCommand
from django.db import connections
from property_info.models import HotelNameDescription

class Command(BaseCommand):
    help = "Change property titles and generate descriptions using Ollama model and save to ollama database"

    def handle(self, *args, **options):
        with connections['travel'].cursor() as cursor:
            cursor.execute("SELECT hotel_id, hotel_name, room_type, location FROM hotels LIMIT 2")
            hotels = cursor.fetchall()

        for hotel_id, hotel_name, room_type, location in hotels:
            try:
                hotel_name_new, description = self.rewrite_title_and_generate_description(hotel_name, room_type, location)
                
                # Create only if we have valid data
                if hotel_name_new and description and description != "Description not available":
                    HotelNameDescription.objects.create(
                        original_id=hotel_id,
                        original_title=hotel_name,
                        rewritten_title=hotel_name_new,
                        description=description
                    )

                    self.stdout.write(self.style.SUCCESS(
                        f"Original: {hotel_name}\nRewritten: {hotel_name_new}\nDescription: {description}\n"
                    ))
                else:
                    self.stdout.write(self.style.WARNING(f"Skipping ID {hotel_id}: Invalid response"))
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
            # Make single request to Ollama
            response = requests.post(
                "http://ollama:11434/api/generate",
                json={
                    "model": "phi",
                    "prompt": prompt,
                    "system": "You are a hotel expert. Respond in the exact format specified.",
                    "stream": False  # Disable streaming for simpler handling
                },
                timeout=None  # Add timeout
            )
            
            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(f"Ollama API error: {response.text}"))
                return None, None

            # Parse the complete response
            response_data = response.json()
            if 'response' not in response_data:
                return None, None

            text = response_data['response']
            
            # Split response into title and description
            try:
                # Strip leading/trailing spaces and newline characters before splitting
                title_part = [line.strip() for line in text.split('\n') if line.startswith('TITLE:')][0]
                desc_part = [line.strip() for line in text.split('\n') if line.startswith('DESCRIPTION:')][0]

                new_title = title_part.replace('TITLE:', '').strip()
                description = desc_part.replace('DESCRIPTION:', '').strip()

                return new_title, description
            except (IndexError, AttributeError) as e:
                self.stdout.write(self.style.WARNING(f"Could not parse response: {e} - {text}"))
                return None, None


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
# docker-compose exec django-new python manage.py rewrite_property_titles