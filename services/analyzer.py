import networkx as nx
from collections import defaultdict

class LeagueAnalyzer:
    def __init__(self, transactions, rosters, users):
        self.transactions = transactions
        self.rosters = rosters
        self.users = users

        # Map roster_id to owner_id
        self.roster_owner_map = {r['roster_id']: r['owner_id'] for r in rosters}

        # Map owner_id to display_name
        self.user_name_map = {u['user_id']: u['display_name'] for u in users}

        # Map roster_id directly to display_name for convenience
        self.roster_name_map = {}
        for rid, oid in self.roster_owner_map.items():
            self.roster_name_map[rid] = self.user_name_map.get(oid, f"Roster {rid}")

    def build_trade_network(self):
        """
        Builds a NetworkX graph where nodes are teams and edges are trades.
        """
        G = nx.Graph()

        # Add nodes
        for rid, name in self.roster_name_map.items():
            # Use name as node identifier to make it readable in visualization
            G.add_node(name, id=rid, label=name)

        trade_counts = defaultdict(int)

        for txn in self.transactions:
            if txn['type'] != 'trade':
                continue

            roster_ids = txn['roster_ids']
            if not roster_ids or len(roster_ids) < 2:
                continue

            # For a trade involving multiple teams, we add edges between all pairs
            # Usually it's just 2 teams
            for i in range(len(roster_ids)):
                for j in range(i + 1, len(roster_ids)):
                    rid1 = roster_ids[i]
                    rid2 = roster_ids[j]

                    name1 = self.roster_name_map.get(rid1, f"Roster {rid1}")
                    name2 = self.roster_name_map.get(rid2, f"Roster {rid2}")

                    # Track trade details
                    key = tuple(sorted((name1, name2)))
                    trade_counts[key] += 1

                    # We can store list of trades as edge attribute
                    if G.has_edge(name1, name2):
                        G[name1][name2]['count'] += 1
                        G[name1][name2]['transactions'].append(txn['transaction_id'])
                    else:
                        G.add_edge(name1, name2, count=1, transactions=[txn['transaction_id']])

        return G

    def get_player_path(self, player_id):
        """
        Traces a player's path through the league based on transactions.
        Returns a list of events: {'date': timestamp, 'from': team, 'to': team, 'type': type}
        """
        events = []

        # Sort transactions by time
        sorted_txns = sorted(self.transactions, key=lambda x: x['created'])

        for txn in sorted_txns:
            adds = txn.get('adds') or {}
            drops = txn.get('drops') or {}

            # Check if player is involved
            if player_id in adds or player_id in drops:
                txn_type = txn['type']
                date = txn['created']

                if txn_type == 'trade':
                    # If traded, they are added to one team and dropped from another (implicitly or explicitly)
                    # Sleeper puts the player in 'adds' for the receiving team
                    # And 'drops' for the sending team? Actually in trades, 'drops' might be null,
                    # but 'adds' tells us who GOT the player.
                    # We need to find who sent the player.
                    # In a trade transaction, 'adds' maps player_id -> roster_id (receiver).
                    # 'drops' maps player_id -> roster_id (sender).
                    # Wait, let's verify sleeper API response structure for trade.
                    # Usually 'adds' has the player. 'drops' might have the player too?
                    # If 'drops' is present, it means the sender dropped them?
                    # In a trade, usually the player is just moved.

                    # If player is in adds:
                    to_roster = adds.get(player_id)
                    from_roster = drops.get(player_id) # Sometimes drops is populated in trade?

                    # If from_roster is missing in drops, we might infer it from previous state
                    # or look at who else is in the transaction.
                    # Actually, for trades, sleeper usually populates both adds and drops?
                    # Or maybe just adds. If just adds, how do we know who sent it?
                    # The transaction has 'roster_ids'. If it's a 2-team trade, the other team sent it.
                    # But if 3-team trade...

                    # Let's handle simple 2-team case mostly.
                    # If drops is present, great.

                    to_team = self.roster_name_map.get(to_roster, "Unknown") if to_roster else "Unknown"
                    from_team = self.roster_name_map.get(from_roster, "Unknown") if from_roster else "Unknown"

                    if not from_roster and len(txn['roster_ids']) == 2 and to_roster:
                         # Infer sender
                         other_roster = [rid for rid in txn['roster_ids'] if rid != to_roster][0]
                         from_team = self.roster_name_map.get(other_roster, "Unknown")

                    events.append({
                        'date': date,
                        'type': 'trade',
                        'from': from_team,
                        'to': to_team,
                        'transaction_id': txn['transaction_id']
                    })

                elif txn_type == 'free_agent' or txn_type == 'waiver':
                    # Add
                    if player_id in adds:
                        to_roster = adds[player_id]
                        to_team = self.roster_name_map.get(to_roster, "Unknown")
                        events.append({
                            'date': date,
                            'type': txn_type, # 'add'
                            'from': "Waivers/FA",
                            'to': to_team,
                            'transaction_id': txn['transaction_id']
                        })
                    # Drop
                    if player_id in drops:
                        from_roster = drops[player_id]
                        from_team = self.roster_name_map.get(from_roster, "Unknown")
                        events.append({
                            'date': date,
                            'type': 'drop',
                            'from': from_team,
                            'to': "Waivers/FA",
                            'transaction_id': txn['transaction_id']
                        })

        return events

    def calculate_stats(self):
        """
        Calculate general league stats.
        """
        stats = {
            'total_trades': 0,
            'most_active_trader': None,
            'biggest_trade': None
        }

        trade_counts = defaultdict(int)
        total_trades = 0

        for txn in self.transactions:
            if txn['type'] == 'trade':
                total_trades += 1
                for rid in txn['roster_ids']:
                    trade_counts[rid] += 1

        stats['total_trades'] = total_trades

        if trade_counts:
            most_active_rid = max(trade_counts, key=trade_counts.get)
            stats['most_active_trader'] = {
                'name': self.roster_name_map.get(most_active_rid, "Unknown"),
                'count': trade_counts[most_active_rid]
            }

        return stats
