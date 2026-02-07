import unittest
from services.analyzer import LeagueAnalyzer
import pandas as pd

class TestLeagueAnalyzer(unittest.TestCase):

    def setUp(self):
        self.users = [
            {'user_id': 'u1', 'display_name': 'Owner1'},
            {'user_id': 'u2', 'display_name': 'Owner2'},
        ]
        self.rosters = [
            {'roster_id': 1, 'owner_id': 'u1'},
            {'roster_id': 2, 'owner_id': 'u2'},
        ]
        self.transactions = [
            {
                'transaction_id': 't1',
                'type': 'trade',
                'roster_ids': [1, 2],
                'adds': {},
                'drops': {},
                'created': 1000
            }
        ]
        self.analyzer = LeagueAnalyzer(self.transactions, self.rosters, self.users)

    def test_get_trade_matrix(self):
        matrix = self.analyzer.get_trade_matrix()

        self.assertIsInstance(matrix, pd.DataFrame)
        self.assertEqual(matrix.shape, (2, 2))
        self.assertIn('Owner1', matrix.index)
        self.assertIn('Owner2', matrix.index)

        # Check trade count
        self.assertEqual(matrix.loc['Owner1', 'Owner2'], 1)
        self.assertEqual(matrix.loc['Owner2', 'Owner1'], 1) # Symmetric
        self.assertEqual(matrix.loc['Owner1', 'Owner1'], 0) # No self trade

if __name__ == '__main__':
    unittest.main()
