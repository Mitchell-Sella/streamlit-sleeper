import unittest
from services.analyzer import LeagueAnalyzer

class TestLeagueAnalyzer(unittest.TestCase):

    def setUp(self):
        self.users = [
            {'user_id': 'u1', 'display_name': 'Owner1'},
            {'user_id': 'u2', 'display_name': 'Owner2'},
            {'user_id': 'u3', 'display_name': 'Owner3'}
        ]
        self.rosters = [
            {'roster_id': 1, 'owner_id': 'u1'},
            {'roster_id': 2, 'owner_id': 'u2'},
            {'roster_id': 3, 'owner_id': 'u3'}
        ]
        self.transactions = [
            {
                'transaction_id': 't1',
                'type': 'trade',
                'status': 'complete',
                'roster_ids': [1, 2],
                'adds': {'p1': 1}, # Owner1 gets p1
                'drops': {'p1': 2}, # Owner2 loses p1
                'created': 1000
            },
            {
                'transaction_id': 't2',
                'type': 'waiver',
                'status': 'complete',
                'roster_ids': [3],
                'adds': {'p2': 3},
                'drops': None,
                'created': 2000
            }
        ]
        self.analyzer = LeagueAnalyzer(self.transactions, self.rosters, self.users)

    def test_build_trade_network(self):
        G = self.analyzer.build_trade_network()
        self.assertTrue(G.has_edge('Owner1', 'Owner2'))
        self.assertEqual(G['Owner1']['Owner2']['count'], 1)
        self.assertFalse(G.has_edge('Owner1', 'Owner3'))

    def test_calculate_stats(self):
        stats = self.analyzer.calculate_stats()
        self.assertEqual(stats['total_trades'], 1)
        # Both Owner1 and Owner2 have 1 trade.
        # Max might pick either, but let's check count is 1.
        self.assertEqual(stats['most_active_trader']['count'], 1)

    def test_get_player_path(self):
        # Transaction t1 moves p1 from Owner2 to Owner1
        # Wait, the logic in get_player_path iterates transactions.
        # t1: Owner2 drops p1, Owner1 adds p1.
        # But 'adds' logic: if p1 in adds, to_roster=1 -> Owner1.
        # If type is trade, we infer from.
        # 'drops' logic: if p1 in drops, from_roster=2 -> Owner2.

        # My implementation handles 'adds' and 'drops' separately in the loop for free_agent/waiver,
        # but combined for 'trade'.

        # Let's see how I implemented it:
        # if txn_type == 'trade':
        #    to_roster = adds.get(player_id)
        #    from_roster = drops.get(player_id)
        #    ... append event ...

        events = self.analyzer.get_player_path('p1')
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['type'], 'trade')
        self.assertEqual(events[0]['from'], 'Owner2') # Inferred from drops or logic
        self.assertEqual(events[0]['to'], 'Owner1')

if __name__ == '__main__':
    unittest.main()
