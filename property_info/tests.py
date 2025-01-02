from unittest import TestCase
import unittest
from unittest import mock
from unittest.mock import patch, MagicMock
from django.db import connections
from django.db import IntegrityError
from django.core.management import call_command
from property_info.management.commands.rewrite_property_titles import Command as RewritePropertyTitlesCommand
from property_info.management.commands.rewrite_property_summary import Command as RewritePropertySummaryCommand
from property_info.management.commands.rewrite_property_rating_review import Command as RewritePropertyRatingReviewCommand
from property_info.models import PropertySummary
from property_info.models import PropertyRatingReview
import requests
import json
from io import StringIO

################# TEST FOR TITLE AND DESCRIPTION STARTS ############################

class TestRewritePropertyTitlesCommand(unittest.TestCase):
    
    @patch('requests.post')
    def test_generate_description(self, mock_post):
        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'response': 'Generated description'}
        mock_post.return_value = mock_response

        # Create an instance of the command
        command = RewritePropertyTitlesCommand()

        # Call the method to generate description
        description = command.generate_description('Test Hotel', 'Suite', 'Downtown')

        # Assert that the description is correctly generated
        self.assertIsNotNone(description)
        self.assertEqual(description, 'Generated description')

    @patch('requests.post')
    def test_generate_description_with_fallback(self, mock_post):
        # Simulate an error from the Ollama API (no 'response' in the API data)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # No 'response' key
        mock_post.return_value = mock_response

        # Create an instance of the command
        command = RewritePropertyTitlesCommand()

        # Call the method to generate description
        description = command.generate_description('Test Hotel', 'Suite', 'Downtown')

        # Test fallback behavior when the API does not return a valid response
        self.assertIsNotNone(description)
        self.assertEqual(description, "Description not available")
    
    @patch('requests.post')
    def test_call_ollama_api_valid_response(self, mock_post):
        # Mock the API response with a valid response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'response': 'Valid description'}
        mock_post.return_value = mock_response

        # Create an instance of the command
        command = RewritePropertyTitlesCommand()

        # Call the method to test
        description = command.call_ollama_api("Sample prompt")

        # Assert that the description is correctly fetched
        self.assertEqual(description, 'Valid description')
    
    @patch('requests.post')
    def test_call_ollama_api_failed_response(self, mock_post):
        # Mock the API response with a non-200 status code
        mock_response = MagicMock()
        mock_response.status_code = 500  # Internal server error
        mock_response.text = 'Server error'
        mock_post.return_value = mock_response

        # Create an instance of the command
        command = RewritePropertyTitlesCommand()

        # Call the method to test
        description = command.call_ollama_api("Sample prompt")

        # Assert that None is returned due to failed response
        self.assertIsNone(description)
    
    @patch('requests.post')
    def test_call_ollama_api_invalid_json(self, mock_post):
        # Mock the API response with an invalid JSON response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
        mock_post.return_value = mock_response

        # Create an instance of the command
        command = RewritePropertyTitlesCommand()

        # Call the method to test
        description = command.call_ollama_api("Sample prompt")

        # Assert that None is returned due to invalid JSON
        self.assertIsNone(description)
    
    @patch('requests.post')
    def test_call_ollama_api_missing_response(self, mock_post):
        # Mock the API response with no 'response' key
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # No 'response' key
        mock_post.return_value = mock_response

        # Create an instance of the command
        command = RewritePropertyTitlesCommand()

        # Call the method to test
        description = command.call_ollama_api("Sample prompt")

        # Assert that None is returned due to missing 'response'
        self.assertIsNone(description)
        
    
    @patch('requests.post')
    @patch('django.db.connections')
    def test_handle_request_exception(self, mock_connections, mock_post):
        """Test handling of request exception during hotel update"""
        # Mock database setup
        mock_cursor = MagicMock()
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_cursor
        mock_connections.__getitem__.return_value.cursor.return_value = mock_cm
        
        # Setup cursor to return one hotel
        mock_cursor.fetchall.return_value = [(1, "Test Hotel", "Suite", "Location")]
        
        # Mock request exception
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")
        
        # Capture stdout
        out = StringIO()
        call_command('rewrite_property_titles', stdout=out)
        
        # Verify error handling
        self.assertIn("Request error: Connection error", out.getvalue())


################# TEST FOR TITLE AND DESCRIPTION ENDS ############################

################# TEST FOR SUMMARY STARTS   #####################################
class TestRewritePropertySummaryCommand(unittest.TestCase):
    def setUp(self):
        PropertySummary.objects.all().delete()

    @mock.patch('requests.post')
    def test_handle(self, mock_post):
        # Mock the API response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'response': 'This is a mock summary.'}

        # Call the management command
        call_command('rewrite_property_summary')

        # Check if the summary was created
        self.assertEqual(PropertySummary.objects.count(), 10)

    @patch('requests.post')
    def test_generate_summary(self, mock_requests):
        # Create an instance of the Command class
        command = RewritePropertySummaryCommand()

        # Mock a successful API response
        mock_requests.return_value.status_code = 200
        mock_requests.return_value.json.return_value = {'response': 'A new hotel summary.'}

        summary = command.generate_summary(
            'Test Hotel', 150, 4.0, 'Suite', 'Downtown', 40.730610, -73.935242
        )

        # Assert that the summary is correctly returned
        self.assertEqual(summary, 'A new hotel summary.')

    @patch('requests.post')
    def test_generate_summary_failure(self, mock_requests):
        # Create an instance of the Command class
        command = RewritePropertySummaryCommand()

        # Mock a failed API response
        mock_requests.return_value.status_code = 500

        summary = command.generate_summary(
            'Test Hotel', 150, 4.0, 'Suite', 'Downtown', 40.730610, -73.935242
        )

        # Assert that None is returned on failure
        self.assertIsNone(summary)

    @mock.patch('requests.post')
    def test_handle_no_summary_generated(self, mock_post):
        # Mock the API response with an empty response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {}

        # Call the management command
        call_command('rewrite_property_summary')

        # Check if no summary was created
        self.assertEqual(PropertySummary.objects.count(), 0)

    @mock.patch('requests.post')
    def test_handle_integration_error(self, mock_post):
        # Mock the API response to raise an exception
        mock_post.side_effect = requests.exceptions.RequestException('Test integration error')

        # Call the management command
        call_command('rewrite_property_summary')

        # Check if no summary was created
        self.assertEqual(PropertySummary.objects.count(), 0)

    @mock.patch('requests.post')
    def test_handle_database_error(self, mock_post):
        # Mock the API response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'response': 'This is a mock summary.'}

        # Mock the database to raise an IntegrityError when executing a query
        with mock.patch.object(connections['default'].cursor(), 'execute') as mock_execute:
            mock_execute.side_effect = IntegrityError('Test database error')

            # Call the management command
            call_command('rewrite_property_summary')

        # Check if no summary was created due to the error
        self.assertEqual(PropertySummary.objects.count(), 10)
    
    @mock.patch('requests.post')
    def test_handle_update_existing_summary(self, mock_post):
        # Create an existing PropertySummary object
        existing_summary = PropertySummary.objects.create(
            property_id='1',
            summary='Old summary'
        )

        # Mock the API response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {'response': 'New summary'}

        # Mock the PropertySummary.objects.filter method to return the existing summary
        with mock.patch.object(PropertySummary.objects, 'filter') as mock_filter:
            mock_filter.return_value.first.return_value = existing_summary

            # Call the management command
            call_command('rewrite_property_summary')

        # Reload the summary from the database after command execution
        updated_summary = PropertySummary.objects.get(property_id='1')

        # Check if the summary was updated
        self.assertEqual(updated_summary.summary, 'New summary')

    
################# TEST FOR SUMMARY ENDS   #####################################

################# TEST FOR RATING REVIEW STARTS   #####################################

class TestRewritePropertyRatingReviewCommand(TestCase):
    def setUp(self):
        self.command = RewritePropertyRatingReviewCommand()

    @patch('property_info.management.commands.rewrite_property_rating_review.requests.post')
    def test_generate_rating_and_review_api_error(self, mock_post):
        # Mock API error response
        mock_post.side_effect = Exception("API error")

        rating, review = self.command.generate_rating_and_review(
            "Test Hotel", 100, "Standard", "New York", 40.7128, -74.0060
        )

        # Assertions
        self.assertEqual(rating, 0.0)
        self.assertEqual(review, "Review not available")

    @patch('property_info.management.commands.rewrite_property_rating_review.connections')
    @patch('property_info.management.commands.rewrite_property_rating_review.PropertyRatingReview')
    def test_handle_existing_rating_review_update(self, mock_model, mock_connections):
        # Mock database query
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, 'Hotel Test', 100, 'Standard', 'New York', 40.7128, -74.0060)
        ]
        mock_connections['travel'].cursor.return_value.__enter__.return_value = mock_cursor

        # Mock existing record
        mock_instance = MagicMock()
        mock_model.objects.filter.return_value.first.return_value = mock_instance

        # Mock generate_rating_and_review method
        self.command.generate_rating_and_review = MagicMock(return_value=(4.5, "Great experience."))

        self.command.handle()

        # Assertions
        mock_instance.save.assert_called_once()
        self.assertEqual(mock_instance.rating, 4.5)
        self.assertEqual(mock_instance.review, "Great experience.")

    @patch('property_info.management.commands.rewrite_property_rating_review.connections')
    @patch('property_info.management.commands.rewrite_property_rating_review.PropertyRatingReview')
    def test_handle_create_new_rating_review(self, mock_model, mock_connections):
        # Mock database query
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, 'Hotel Test', 100, 'Standard', 'New York', 40.7128, -74.0060)
        ]
        mock_connections['travel'].cursor.return_value.__enter__.return_value = mock_cursor

        # Mock no existing record
        mock_model.objects.filter.return_value.first.return_value = None

        # Mock generate_rating_and_review method
        self.command.generate_rating_and_review = MagicMock(return_value=(4.5, "Amazing stay."))

        self.command.handle()

        # Assertions
        mock_model.objects.create.assert_called_once_with(
            property_id=1,
            rating=4.5,
            review="Amazing stay."
        )

    @patch('property_info.management.commands.rewrite_property_rating_review.connections')
    @patch('property_info.management.commands.rewrite_property_rating_review.PropertyRatingReview')
    @patch('property_info.management.commands.rewrite_property_rating_review.requests.post')
    def test_handle_api_failure_fallback(self, mock_post, mock_model, mock_connections):
        # Mock database query
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, 'Hotel Test', 100, 'Standard', 'New York', 40.7128, -74.0060)
        ]
        mock_connections['travel'].cursor.return_value.__enter__.return_value = mock_cursor

        # Mock API failure
        mock_post.side_effect = Exception("API failure")

        # Mock no existing record
        mock_model.objects.filter.return_value.first.return_value = None

        self.command.handle()

        # Assertions
        mock_model.objects.create.assert_called_once_with(
            property_id=1,
            rating=0.0,
            review="Review not available"
        )


    @patch('property_info.management.commands.rewrite_property_rating_review.requests.post')
    def test_generate_rating_and_review_rating_extraction_failure(self, mock_post):
        # Mock a successful API response but with no rating
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'response': 'Review: Noisy neighbors and poor service.'
        }
        mock_post.return_value = mock_response

        rating, review = self.command.generate_rating_and_review(
            "Test Hotel", 100, "Standard", "New York", 40.7128, -74.0060
        )

        # Assertions
        self.assertEqual(rating, 0.0)
        self.assertEqual(review, "Noisy neighbors and poor service.")


    @patch('property_info.management.commands.rewrite_property_rating_review.connections')
    @patch('property_info.management.commands.rewrite_property_rating_review.PropertyRatingReview')
    def test_handle_no_hotels(self, mock_model, mock_connections):
        # Mock database query to return no hotels
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_connections['travel'].cursor.return_value.__enter__.return_value = mock_cursor

        self.command.handle()

        # Assertions
        mock_model.objects.filter.assert_not_called()

    @patch('property_info.management.commands.rewrite_property_rating_review.requests.post')
    def test_generate_rating_and_review_timeout(self, mock_post):
        # Mock a timeout exception
        mock_post.side_effect = requests.exceptions.Timeout

        rating, review = self.command.generate_rating_and_review(
            "Test Hotel", 100, "Standard", "New York", 40.7128, -74.0060
        )

        # Assertions
        self.assertEqual(rating, 0.0)
        self.assertEqual(review, "Review not available")
        
################# TEST FOR RATING REVIEW ENDS   #####################################

  
if __name__ == '__main__':
    unittest.main()