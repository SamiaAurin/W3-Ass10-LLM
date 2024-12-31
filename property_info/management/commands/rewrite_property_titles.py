# this is property_info/management/commands/rewrite_property_titles.py
########################################

import requests
import json
from django.core.management.base import BaseCommand
from django.db import connections
import re


class Command(BaseCommand):
    help = "Change property titles and generate descriptions using Ollama model and update the hotels table"

    def handle(self, *args, **options):
        with connections['travel'].cursor() as cursor:
            # Dynamically add a `description` column if it doesn't exist
            cursor.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 
                        FROM information_schema.columns 
                        WHERE table_name='hotels' AND column_name='description'
                    ) THEN
                        ALTER TABLE hotels ADD COLUMN description TEXT;
                    END IF;
                END $$;
            """)

            # Fetch hotel data
            cursor.execute("SELECT hotel_id, hotel_name, room_type, location FROM hotels LIMIT 2")
            hotels = cursor.fetchall()

        for hotel_id, hotel_name, room_type, location in hotels:
            try:
                # Generate new title and description
                hotel_name_new, description = self.rewrite_title_and_generate_description(hotel_name, room_type, location)

                # Handle fallback if parsing fails
                if hotel_name_new is None or description is None:
                    self.stdout.write(self.style.WARNING(f"Could not parse response for ID {hotel_id}. Using fallback data."))
                    hotel_name_new = "Could not parse the name"
                    description = "Description not available"

                # Update the `hotels` table directly
                with connections['travel'].cursor() as cursor:
                    cursor.execute("""
                        UPDATE hotels
                        SET hotel_name = %s, description = %s
                        WHERE hotel_id = %s
                    """, [hotel_name_new, description, hotel_id])

                self.stdout.write(self.style.SUCCESS(
                    f"Updated ID {hotel_id}:\nOriginal Name: {hotel_name}\nRewritten Name: {hotel_name_new}\nDescription: {description}\n"
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
            response = requests.post(
                "http://ollama:11434/api/generate",
                json={
                    "model": "tinyllama",
                    "prompt": prompt,
                    "system": "You are a hotel expert. Respond in the exact format specified.",
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

            # Extract TITLE and DESCRIPTION using regex
            title_match = re.search(r'^TITLE:\s*(.+)', text, re.IGNORECASE | re.MULTILINE)
            description_match = re.search(r'^DESCRIPTION:\s*(.+)', text, re.IGNORECASE | re.MULTILINE)

            if not title_match or not description_match:
                self.stdout.write(self.style.WARNING(f"Could not parse response: {text}"))
                return None, None

            new_title = title_match.group(1).strip()
            description = description_match.group(1).strip()

            if not new_title or not description:
                self.stdout.write(self.style.WARNING(f"Empty title or description in response: {text}"))
                return None, None

            return new_title, description

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