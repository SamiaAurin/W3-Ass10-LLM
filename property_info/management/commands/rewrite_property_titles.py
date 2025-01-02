import requests
import json
from django.core.management.base import BaseCommand
from django.db import connections, transaction

class Command(BaseCommand):
    help = "Change property titles and generate descriptions using Ollama model and update the hotels table"

    def handle(self, *args, **options):
        try:
            # Dynamically add the `description` column if it doesn't exist
            with connections['travel'].cursor() as cursor:
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
            with connections['travel'].cursor() as cursor:
                cursor.execute("SELECT hotel_id, hotel_name, room_type, location FROM hotels WHERE hotel_id IS NOT NULL LIMIT 2")
                hotels = cursor.fetchall()

            for hotel_id, hotel_name, room_type, location in hotels:
                try:
                    # Generate new title and description
                    hotel_name_new = self.rewrite_title(hotel_name)
                    description = self.generate_description(hotel_name, room_type, location)

                    # Handle fallback if parsing fails
                    if hotel_name_new is None or description is None:
                        self.stdout.write(self.style.WARNING(
                            f"Could not parse response for hotel ID {hotel_id}. Using fallback data."
                        ))
                        hotel_name_new = "Name unavailable"
                        description = "Description not available"

                    # Update the `hotels` table
                    with connections['travel'].cursor() as cursor, transaction.atomic():
                        cursor.execute("""
                            UPDATE hotels
                            SET hotel_name = %s, description = %s
                            WHERE hotel_id = %s
                        """, [hotel_name_new, description, hotel_id])

                    self.stdout.write(self.style.SUCCESS(
                        f"Updated hotel ID {hotel_id}:\n"
                        f"Original Name: {hotel_name}\n"
                        f"Rewritten Name: {hotel_name_new}\n"
                        f"Description: {description}\n"
                    ))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f"Error processing hotel ID {hotel_id}: {str(e)}"
                    ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Critical error: {str(e)}"))

    def rewrite_title(self, title):
        prompt = f"""Create a unique hotel name for this hotel {title} within maximum 4 words.""" 

        return self.call_ollama_api(prompt)

    def generate_description(self, title, room_type, location):
        prompt = f"""Create a description in 30 words. 

                    Using these informations
                    - Current name: {title}
                    - Room type: {room_type}
                    - Location: {location}"""

        description = self.call_ollama_api(prompt)

        # Fallback logic: if description is None, return a default message
        if not description:
            return "Description not available"

        return description


    def call_ollama_api(self, prompt):
        try:
            response = requests.post(
                "http://ollama:11434/api/generate",
                json={
                    "model": "phi",  # or `phi` if you have installed `phi`
                    "prompt": prompt,
                    "system": "You are a hotel expert. Respond in a concise, informative way.",
                    "stream": False
                },
                timeout=None
            )
            
            #print(f"Response Status: {response.status_code}")  # Debugging line
            #print(f"Response Data: {response.json()}")  # Debugging line

            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(f"Ollama API error: {response.text}"))
                return None

            response_data = response.json()
            if 'response' not in response_data or not response_data['response']:
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

    