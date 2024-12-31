from django.test import TestCase
from unittest.mock import patch
from django.core.management import call_command
from property_info.models import PropertySummary
from django.db import connections
from io import StringIO

class CommandTestCase(TestCase):

    def setUp(self):
        # Prepare test data in the hotels table (using mock data for testing)
        self.test_hotel_data = {
            'hotel_id': 1,
            'hotel_name': 'Test Hotel',
            'price': 100.00,
            'rating': 4.5,
            'room_type': 'Deluxe Room',
            'location': 'Test Location',
            'latitude': 12.3456,
            'longitude': 78.9101,
        }

        # Insert mock hotel data into the 'travel' database for testing
        with connections['travel'].cursor() as cursor:
            cursor.execute("""
                INSERT INTO hotels_data.hotels (hotel_id, hotel_name, price, rating, room_type, location, latitude, longitude)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                self.test_hotel_data['hotel_id'],
                self.test_hotel_data['hotel_name'],
                self.test_hotel_data['price'],
                self.test_hotel_data['rating'],
                self.test_hotel_data['room_type'],
                self.test_hotel_data['location'],
                self.test_hotel_data['latitude'],
                self.test_hotel_data['longitude']
            ])

    @patch('property_info.management.commands.rewrite_property_summary.requests.post')
    def test_rewrite_property_summary_command(self, mock_post):
        # Mock the response from the Ollama API
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'response': 'Test summary generated successfully.'}

        # Capture the command output
        output = StringIO()
        
        # Call the management command
        call_command('rewrite_property_summary', stdout=output)

        # Check if the success message is in the output
        self.assertIn("Created new summary for Test Hotel", output.getvalue())

        # Verify that a new PropertySummary record has been created
        property_summary = PropertySummary.objects.get(property_id=self.test_hotel_data['hotel_id'])
        self.assertEqual(property_summary.summary, 'Test summary generated successfully.')

    @patch('property_info.management.commands.rewrite_property_summary.requests.post')
    def test_update_existing_summary(self, mock_post):
        # Mock the response from the Ollama API
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'response': 'Updated summary successfully.'}

        # Insert an initial PropertySummary for the hotel to be updated
        PropertySummary.objects.create(
            property_id=self.test_hotel_data['hotel_id'],
            summary='Old summary'
        )

        # Capture the command output
        output = StringIO()

        # Call the management command
        call_command('rewrite_property_summary', stdout=output)

        # Check if the update message is in the output
        self.assertIn("Updated summary for Test Hotel", output.getvalue())

        # Verify that the existing PropertySummary record has been updated
        property_summary = PropertySummary.objects.get(property_id=self.test_hotel_data['hotel_id'])
        self.assertEqual(property_summary.summary, 'Updated summary successfully.')

    @patch('property_info.management.commands.rewrite_property_summary.requests.post')
    def test_no_summary_generated(self, mock_post):
        # Mock the response from the Ollama API (simulating a failure to generate a summary)
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {}

        # Capture the command output
        output = StringIO()

        # Call the management command
        call_command('rewrite_property_summary', stdout=output)

        # Check for the warning message in case of failure to generate summary
        self.assertIn("Could not generate summary for hotel ID", output.getvalue())

    @patch('property_info.management.commands.rewrite_property_summary.requests.post')
    def test_api_request_error(self, mock_post):
        # Mock the response from the Ollama API (simulating a request error)
        mock_post.side_effect = Exception('API request error')

        # Capture the command output
        output = StringIO()

        # Call the management command
        call_command('rewrite_property_summary', stdout=output)

        # Check for the error message due to request failure
        self.assertIn("Request error:", output.getvalue())

    def tearDown(self):
        # Clean up the test data
        with connections['travel'].cursor() as cursor:
            cursor.execute("DELETE FROM hotels_data.hotels WHERE hotel_id = %s", [self.test_hotel_data['hotel_id']])
        PropertySummary.objects.filter(property_id=self.test_hotel_data['hotel_id']).delete()
