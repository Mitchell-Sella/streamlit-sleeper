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

    @patch('services.sleeper.SleeperService.get_league')
    def test_get_league_history(self, mock_get_league):
        # Mock get_league to return previous_league_id
        def side_effect(league_id):
            if league_id == "current":
                return {"league_id": "current", "previous_league_id": "prev"}
            if league_id == "prev":
                return {"league_id": "prev", "previous_league_id": None}
            return None

        mock_get_league.side_effect = side_effect

        history = SleeperService.get_league_history("current")
        self.assertEqual(history, ["current", "prev"])

if __name__ == '__main__':
    unittest.main()
