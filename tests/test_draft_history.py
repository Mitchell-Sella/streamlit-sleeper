import unittest
from collections import defaultdict

# Mock the function from pages/2_Draft_History.py
# Since it's inside a streamlit script, I'll replicate the logic here for testing
# or import it if I structure it as a utility.
# For now, I'll copy the logic function `process_draft_history` to test it.

class MockAnalyzer:
    def __init__(self):
        self.user_name_map = {'u1': 'User 1'}
    def get_player_name(self, pid):
        return f"Player {pid}"

def process_draft_history(draft_data, selected_user_id, analyzer_instance):
    grid_counts = defaultdict(int)
    player_history_list = []

    for entry in draft_data:
        draft = entry['draft']
        season = draft.get('season')
        picks = entry['picks']

        sorted_picks = sorted(picks, key=lambda x: x.get('pick_no', x.get('draft_slot', 0)))

        round_counters = defaultdict(int)

        for pick in sorted_picks:
            p_round = pick.get('round')
            round_counters[p_round] += 1
            p_in_round = round_counters[p_round]

            if pick.get('picked_by') == selected_user_id:
                grid_counts[(p_round, p_in_round)] += 1

                pid = pick.get('player_id')
                p_name = analyzer_instance.get_player_name(pid)

                player_history_list.append({
                    'Season': season,
                    'Round': p_round,
                    'Pick': p_in_round,
                    'Slot': f"{p_round}.{p_in_round:02d}",
                    'Player': p_name
                })

    return grid_counts, player_history_list

class TestDraftHistoryLogic(unittest.TestCase):
    def test_process_draft_history(self):
        draft_data = [
            {
                'draft': {'season': '2024'},
                'picks': [
                    {'round': 1, 'pick_no': 1, 'picked_by': 'u1', 'player_id': 'p1'}, # 1.01
                    {'round': 1, 'pick_no': 2, 'picked_by': 'u2', 'player_id': 'p2'}, # 1.02
                    {'round': 2, 'pick_no': 3, 'picked_by': 'u1', 'player_id': 'p3'}, # 2.01 (1st in round 2)
                ]
            }
        ]

        analyzer = MockAnalyzer()
        grid, history = process_draft_history(draft_data, 'u1', analyzer)

        # Verify Grid
        # u1 picked at 1.01 and 2.01
        self.assertEqual(grid[(1, 1)], 1)
        self.assertEqual(grid[(2, 1)], 1)
        self.assertEqual(grid[(1, 2)], 0) # u2 picked here

        # Verify History List
        self.assertEqual(len(history), 2)

        p1 = history[0]
        self.assertEqual(p1['Slot'], '1.01')
        self.assertEqual(p1['Player'], 'Player p1')

        p2 = history[1]
        self.assertEqual(p2['Slot'], '2.01')
        self.assertEqual(p2['Player'], 'Player p3')

if __name__ == '__main__':
    unittest.main()
