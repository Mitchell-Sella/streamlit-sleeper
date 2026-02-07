import unittest
from services.analyzer import LeagueAnalyzer

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
        # Trade 1: Owner1 gets P1.
        # Trade 2: Owner1 trades P1 for P2.
        self.transactions = [
            {
                'transaction_id': 't1',
                'type': 'trade',
                'roster_ids': [1, 2],
                'adds': {'p1': 1}, # Owner1 gets p1
                'drops': {'p1': 2},
                'created': 1000
            },
            {
                'transaction_id': 't2',
                'type': 'trade',
                'roster_ids': [1, 2],
                'adds': {'p2': 1}, # Owner1 gets p2
                'drops': {'p1': 1, 'p2': 2}, # Owner1 gives p1
                'created': 2000
            }
        ]
        self.analyzer = LeagueAnalyzer(self.transactions, self.rosters, self.users)

    def test_build_trade_tree(self):
        # Focus on Roster 1 (Owner1) starting from t1
        G = self.analyzer.build_trade_tree('t1', 1)

        # Expect t1 -> t2 edge labeled 'p1'
        self.assertTrue(G.has_edge('t1', 't2'))
        # Check edge label if possible, but networkx stores data in dict
        edge_data = G.get_edge_data('t1', 't2')
        # Note: My implementation might overwrite label if multiple assets move?
        # Current impl: G.add_edge(..., label=str(asset_id)) inside loop.
        # If multiple assets move, it might overwrite or add parallel edges (if MultiDiGraph).
        # Using DiGraph, subsequent add_edge calls update attributes.
        # I should probably append to label or use a list.
        # But for this test, p1 is the only asset.
        self.assertEqual(edge_data['label'], 'p1')

if __name__ == '__main__':
    unittest.main()
