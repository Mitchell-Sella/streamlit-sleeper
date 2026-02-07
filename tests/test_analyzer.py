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

    def test_get_trade_matrix_symmetric(self):
        # No creator field
        transactions = [
            {
                'transaction_id': 't1',
                'type': 'trade',
                'roster_ids': [1, 2],
                'created': 1000
            }
        ]
        analyzer = LeagueAnalyzer(transactions, self.rosters, self.users)
        matrix = analyzer.get_trade_matrix()

        self.assertEqual(matrix.loc['Owner1', 'Owner2'], 1)
        self.assertEqual(matrix.loc['Owner2', 'Owner1'], 1)

    def test_get_trade_matrix_asymmetric(self):
        # With creator field
        transactions = [
            {
                'transaction_id': 't1',
                'type': 'trade',
                'roster_ids': [1, 2],
                'creator': 'u1', # Owner1 is creator
                'created': 1000
            }
        ]
        analyzer = LeagueAnalyzer(transactions, self.rosters, self.users)
        matrix = analyzer.get_trade_matrix()

        # Row=Sender, Col=Acceptor
        # Owner1 proposed, Owner2 accepted
        self.assertEqual(matrix.loc['Owner1', 'Owner2'], 1)
        # Owner2 did NOT propose to Owner1
        self.assertEqual(matrix.loc['Owner2', 'Owner1'], 0)

if __name__ == '__main__':
    unittest.main()
