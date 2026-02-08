import unittest
from services.analyzer import LeagueAnalyzer

class TestDraftResolutionLabels(unittest.TestCase):
    def test_draft_label_generation(self):
        # Mock Draft Data
        # 3 picks in Round 1
        draft_data = [
            {
                'draft': {
                    'season': '2025',
                    'slot_to_roster_id': { "1": 1, "2": 2, "3": 3 }
                },
                'picks': [
                    {'round': 1, 'draft_slot': 1, 'pick_no': 1, 'player_id': 'p1', 'roster_id': 1},
                    {'round': 1, 'draft_slot': 2, 'pick_no': 2, 'player_id': 'p2', 'roster_id': 2},
                    {'round': 2, 'draft_slot': 1, 'pick_no': 3, 'player_id': 'p3', 'roster_id': 1}, # 2.01 (3rd overall in 2 team league? no logic is independent of team count)
                ]
            }
        ]

        # My logic counts picks per round to determine label.
        # Pick 1 (Round 1) -> 1.01
        # Pick 2 (Round 1) -> 1.02
        # Pick 3 (Round 2) -> 2.01

        analyzer = LeagueAnalyzer([], [], [])
        analyzer.initialize_drafts(draft_data)

        # Verify 1.01
        key1 = ('2025', 1, 1) # Season 2025, Round 1, Org Owner 1 (Slot 1)
        self.assertIn(key1, analyzer.pick_map)
        self.assertEqual(analyzer.pick_map[key1]['label'], '1.01')

        # Verify 1.02
        key2 = ('2025', 1, 2) # Org Owner 2 (Slot 2)
        self.assertIn(key2, analyzer.pick_map)
        self.assertEqual(analyzer.pick_map[key2]['label'], '1.02')

        # Verify 2.01
        key3 = ('2025', 2, 1) # Org Owner 1 (Slot 1)
        self.assertIn(key3, analyzer.pick_map)
        self.assertEqual(analyzer.pick_map[key3]['label'], '2.01')

    def test_trade_enrichment_format(self):
        # Mock Transactions
        transactions = [
            {
                'transaction_id': 'txn1',
                'type': 'trade',
                'created': 1000,
                'roster_ids': [1, 2],
                'draft_picks': [
                    {
                        'season': '2025',
                        'round': 1,
                        'roster_id': 1,
                        'owner_id': 2,
                    }
                ],
                'adds': {'p1': 2}, # Player p1 goes to 2
                'drops': {}
            }
        ]

        rosters = [{'roster_id': 1, 'owner_id': 'u1'}, {'roster_id': 2, 'owner_id': 'u2'}]
        users = [{'user_id': 'u1', 'display_name': 'A'}, {'user_id': 'u2', 'display_name': 'B'}]
        players = {'p1': {'first_name': 'Caleb', 'last_name': 'Williams', 'position': 'QB', 'team': 'CHI'}}

        analyzer = LeagueAnalyzer(transactions, rosters, users, players)

        # Inject pick map manually
        analyzer.pick_map = {
            ('2025', 1, 1): {'player': 'Caleb Williams', 'label': '1.01'}
        }

        enriched = analyzer.get_enriched_trades(transactions, None, None)
        trade = enriched[0]

        # Check Player Format (No details)
        # p1 was added to roster 2.
        # "Caleb Williams" should appear in accepter_receives (assuming 2 is accepter)

        # Identify who is who. Roster 1 -> A, Roster 2 -> B.
        # txn creator is None.
        # Logic: if not creator, pick first as proposer. Proposer=1. Accepter=2.

        # Roster 2 receives pick and player.
        # So Accepter receives.

        receives = trade['accepter_receives']

        # Check Player
        player_str = "**Caleb Williams**"
        self.assertIn(player_str, receives)
        # Ensure no details
        for r in receives:
            if "Caleb Williams" in r:
                self.assertNotIn("QB - CHI", r)

        # Check Pick
        pick_str = "**2025 1.01** (Selected: Caleb Williams)"
        self.assertIn(pick_str, receives)

if __name__ == '__main__':
    unittest.main()
