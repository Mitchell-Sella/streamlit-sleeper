import networkx as nx
from collections import defaultdict

class LeagueAnalyzer:
    def __init__(self, transactions, rosters, users, all_players=None):
        self.transactions = transactions
        self.rosters = rosters
        self.users = users
        self.all_players = all_players or {}

        # Map roster_id to owner_id
        self.roster_owner_map = {r['roster_id']: r['owner_id'] for r in rosters}

        # Map owner_id to display_name
        self.user_name_map = {u['user_id']: u['display_name'] for u in users}

        # Map roster_id directly to display_name for convenience
        self.roster_name_map = {}
        for rid, oid in self.roster_owner_map.items():
            self.roster_name_map[rid] = self.user_name_map.get(oid, f"Roster {rid}")

    def get_player_name(self, player_id):
        """Helper to resolve player ID to name."""
        if not player_id:
            return "Unknown"
        # Try to cast to string just in case
        player_id = str(player_id)
        if player_id in self.all_players:
            p = self.all_players[player_id]
            return f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
        return player_id

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
                    to_roster = adds.get(player_id)
                    from_roster = drops.get(player_id)

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

    def get_trades_for_roster(self, roster_id):
        """Get all trades involving a specific roster."""
        trades = []
        for txn in self.transactions:
            if txn['type'] == 'trade' and roster_id in txn['roster_ids']:
                trades.append(txn)
        return sorted(trades, key=lambda x: x['created'], reverse=True)

    def build_trade_tree(self, root_transaction_id, focal_roster_id):
        """
        Builds a tree of trades starting from a root transaction.
        Tracks assets acquired by focal_roster_id and sees where they go.
        """
        # Find root transaction
        root_txn = next((t for t in self.transactions if t['transaction_id'] == root_transaction_id), None)
        if not root_txn:
            return None

        # Initialize graph
        G = nx.DiGraph()

        # Sort all transactions by date to search forward
        sorted_txns = sorted(self.transactions, key=lambda x: x['created'])

        # Helper to recursively find next trades
        def trace_assets(current_txn, current_assets):
            current_id = current_txn['transaction_id']
            # We add node if not exists (or update attributes)
            if not G.has_node(current_id):
                G.add_node(current_id, label=f"Trade {current_id}", data=current_txn)

            # Identify where 'current_txn' is in the list
            try:
                start_idx = sorted_txns.index(current_txn) + 1
            except ValueError:
                return

            # For each asset acquired in this transaction...
            for asset_id in current_assets:
                found_next = False
                # Scan future transactions
                for i in range(start_idx, len(sorted_txns)):
                    next_txn = sorted_txns[i]

                    # Must involve our focal roster
                    if focal_roster_id not in next_txn['roster_ids']:
                        continue

                    # Check if asset_id is dropped/traded away
                    drops = next_txn.get('drops') or {}

                    if asset_id in drops:
                        # Found the move!
                        found_next = True

                        if next_txn['type'] == 'trade':
                            # It's a trade branch
                            next_id = next_txn['transaction_id']

                            # Determine what we got in return (new assets)
                            adds = next_txn.get('adds') or {}
                            new_assets = [pid for pid, rid in adds.items() if rid == focal_roster_id]

                            # Resolve asset name
                            asset_name = self.get_player_name(asset_id)

                            # Add edge
                            G.add_edge(current_id, next_id, label=asset_name)

                            # Recurse
                            trace_assets(next_txn, new_assets)
                        else:
                            # It was dropped/waivered
                            # Optional: Add a 'Drop' node?
                            pass

                        break # Asset moved, stop searching for this asset

                if not found_next:
                    # Asset stays on roster
                    pass

        # Initial assets: What did focal_roster_id GET in root_txn?
        adds = root_txn.get('adds') or {}
        # In a trade, adds dictionary maps player_id -> roster_id (receiver)
        initial_assets = [pid for pid, rid in adds.items() if rid == focal_roster_id]

        trace_assets(root_txn, initial_assets)

        return G
