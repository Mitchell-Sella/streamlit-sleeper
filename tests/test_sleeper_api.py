import unittest
from unittest.mock import patch, MagicMock
from services.sleeper import SleeperService

class TestSleeperService(unittest.TestCase):

    @patch('services.sleeper.requests.get')
    def test_get_user(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"username": "testuser", "user_id": "123"}
        mock_get.return_value = mock_response

        user = SleeperService.get_user("testuser")
        self.assertEqual(user['username'], "testuser")
        self.assertEqual(user['user_id'], "123")

    @patch('services.sleeper.requests.get')
    def test_get_all_leagues(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"league_id": "1001", "name": "Dynasty League"}]
        mock_get.return_value = mock_response

        leagues = SleeperService.get_all_leagues("123")
        self.assertEqual(len(leagues), 1)
        self.assertEqual(leagues[0]['league_id'], "1001")

    @patch('services.sleeper.requests.get')
    def test_get_transactions(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"transaction_id": "tx1", "type": "trade"}]
        mock_get.return_value = mock_response

        transactions = SleeperService.get_transactions("1001", 1)
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0]['transaction_id'], "tx1")

if __name__ == '__main__':
    unittest.main()
