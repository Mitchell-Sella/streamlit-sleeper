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
        # Chain:
        # T1 (1000): Owner 1 adds P1 (FA)
        # T2 (2000): Owner 1 trades P1 to Owner 2
        # T3 (3000): Owner 2 trades P1 back to Owner 1 (or someone else)

        self.transactions = [
            {
                'transaction_id': 't1',
                'type': 'free_agent',
                'roster_ids': [1],
                'adds': {'p1': 1},
                'drops': {},
                'created': 1000
            },
            {
                'transaction_id': 't2',
                'type': 'trade',
                'roster_ids': [1, 2],
                'adds': {'p1': 2}, # Owner 2 gets p1
                'drops': {'p1': 1}, # Owner 1 gives p1
                'created': 2000
            },
            {
                'transaction_id': 't3',
                'type': 'trade',
                'roster_ids': [1, 2],
                'adds': {'p1': 1}, # Owner 1 gets p1 back
                'drops': {'p1': 2}, # Owner 2 gives p1
                'created': 3000
            }
        ]
        self.analyzer = LeagueAnalyzer(self.transactions, self.rosters, self.users)

    def test_build_trade_tree_full_history(self):
        # Selecting the middle trade (t2) should show upstream (t1) and downstream (t3)
        G = self.analyzer.build_trade_tree('t2')

        self.assertIsNotNone(G)
        self.assertTrue(G.has_node('t1'))
        self.assertTrue(G.has_node('t2'))
        self.assertTrue(G.has_node('t3'))

        self.assertTrue(G.has_edge('t1', 't2'))
        self.assertTrue(G.has_edge('t2', 't3'))

        # Check edge labels (should contain asset name/ID)
        # Since no player name map, it uses ID
        # Label logic: label=asset_name
        # For t1->t2, p1 moves.
        # For t2->t3, p1 moves.

        # Note: In my impl, I don't set G.edge['label'] directly if using multi-edges or if logic appends.
        # But let's check attributes
        edge_t1_t2 = G[u't1'][u't2']
        self.assertIn('p1', edge_t1_t2['label'])

if __name__ == '__main__':
    unittest.main()
