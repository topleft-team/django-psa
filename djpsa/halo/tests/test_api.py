import unittest
from unittest.mock import patch, MagicMock
from djpsa.halo.api import HaloAPIClient


class TestHaloAPIClient(unittest.TestCase):

    @patch('djpsa.halo.api.requests.request')
    @patch('djpsa.halo.api.HaloAPITokenFetcher.get_token',
           return_value='test_token')
    def test_request_success(self, _, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        client = HaloAPIClient()
        response = client._request('GET', 'http://example.com')

        self.assertEqual(response, mock_response)
        mock_request.assert_called_once_with(
            'GET',
            'http://example.com',
            headers={'Authorization': 'Bearer test_token'},
            params=None,
            timeout=30.0
        )

    @patch('djpsa.halo.api.requests.request')
    @patch('djpsa.halo.api.HaloAPITokenFetcher.get_token')
    def test_request_token_refresh(
            self, mock_get_token, mock_request):
        mock_get_token.side_effect = ['expired_token', 'new_token']
        mock_response_401 = MagicMock()
        mock_response_401.status_code = 401
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_request.side_effect = [mock_response_401, mock_response_200]

        client = HaloAPIClient()
        response = client._request('GET', 'http://example.com')

        self.assertEqual(response, mock_response_200)
        self.assertEqual(mock_get_token.call_count, 2)
        self.assertEqual(mock_request.call_count, 2)
        mock_request.assert_called_with(
            'GET',
            'http://example.com',
            headers={'Authorization': 'Bearer new_token'},
            params=None
        )


class TestPrepareErrorResponse(unittest.TestCase):
    """Halo has no standard error format, so the single-key fallback has to
    cope with whatever type the value happens to be."""

    def _error(self, content):
        response = MagicMock()
        response.content = content.encode('utf-8')
        return HaloAPIClient()._prepare_error_response(response)

    def test_single_key_string_value(self):
        self.assertEqual(self._error('{"error": "Bad request"}'),
                         'Error: Bad request')

    def test_single_key_list_value(self):
        # A rejected field write comes back as a list. This used to raise
        # AttributeError from .replace(), losing the message it was handed.
        self.assertEqual(
            self._error('{"errors": ["Error converting value 36."]}'),
            "[Error converting value 36.]")

    def test_unparseable_content(self):
        self.assertIn('An error occurred', self._error('not json'))
