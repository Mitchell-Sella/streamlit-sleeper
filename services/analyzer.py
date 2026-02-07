import networkx as nx
from collections import defaultdict
import pandas as pd
import time

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

        # Transaction map for quick lookup
        self.txn_map = {t['transaction_id']: t for t in self.transactions}

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

    def get_trade_matrix(self):
        """
        Returns a pandas DataFrame representing the trade matrix.
        If 'creator' info is reliable, Rows=Proposers, Cols=Accepters.
        Otherwise, symmetric.
        """
        team_names = sorted(list(self.roster_name_map.values()))
        matrix = pd.DataFrame(0, index=team_names, columns=team_names)

        # Check if we have creators in any trade
        has_creator = False
        for txn in self.transactions:
            if txn['type'] == 'trade' and txn.get('creator'):
                has_creator = True
                break

        for txn in self.transactions:
            if txn['type'] != 'trade':
                continue

            roster_ids = txn['roster_ids']
            if not roster_ids or len(roster_ids) < 2:
                continue

            creator_id = txn.get('creator')

            # Identify Proposer Roster
            proposer_rid = None
            if has_creator and creator_id:
                for rid in roster_ids:
                    if self.roster_owner_map.get(rid) == creator_id:
                        proposer_rid = rid
                        break

            if has_creator and proposer_rid:
                # Asymmetric: Proposer (Row) -> Accepter (Col)
                row_name = self.roster_name_map.get(proposer_rid)

                for rid in roster_ids:
                    if rid == proposer_rid:
                        continue
                    col_name = self.roster_name_map.get(rid)

                    if row_name in matrix.index and col_name in matrix.columns:
                        matrix.loc[row_name, col_name] += 1
            else:
                # Symmetric fallback
                for i in range(len(roster_ids)):
                    for j in range(i + 1, len(roster_ids)):
                        rid1 = roster_ids[i]
                        rid2 = roster_ids[j]

                        name1 = self.roster_name_map.get(rid1, f"Roster {rid1}")
                        name2 = self.roster_name_map.get(rid2, f"Roster {rid2}")

                        if name1 in matrix.index and name2 in matrix.columns:
                            matrix.loc[name1, name2] += 1
                            matrix.loc[name2, name1] += 1

        return matrix

    def get_player_path(self, player_id):
        """
        Traces a player's path through the league based on transactions.
        Returns a list of events: {'date': timestamp, 'from': team, 'to': team, 'type': type, 'transaction_id': tid}
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
                tid = txn['transaction_id']

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
                        'transaction_id': tid
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
                            'transaction_id': tid
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
                            'transaction_id': tid
                        })

        return events

    def calculate_stats(self):
        """
        Calculate general league stats.
        """
        stats = {
            'total_trades': 0,
            'most_active_trader': None,
            'least_active_trader': None,
            'days_since_last_trade': None
        }

        trade_counts = defaultdict(int)
        total_trades = 0
        last_trade_time = 0

        for txn in self.transactions:
            if txn['type'] == 'trade':
                total_trades += 1
                created = txn.get('created', 0)
                if created > last_trade_time:
                    last_trade_time = created

                for rid in txn['roster_ids']:
                    trade_counts[rid] += 1

        stats['total_trades'] = total_trades

        if trade_counts:
            # Most Active
            most_active_rid = max(trade_counts, key=trade_counts.get)
            stats['most_active_trader'] = {
                'name': self.roster_name_map.get(most_active_rid, "Unknown"),
                'count': trade_counts[most_active_rid]
            }

            # Least Active (exclude 0 if we assume only looking at those who traded,
            # or include all if we want to shame non-traders. Let's include those with > 0 first)
            # Actually, user probably wants to see who trades the least (maybe 0).
            # But trade_counts only has those who traded.

            # Find min > 0
            min_count = min(trade_counts.values())
            # Find who has that count
            least_active_rids = [rid for rid, count in trade_counts.items() if count == min_count]
            # Just take the first one or format
            least_active_name = self.roster_name_map.get(least_active_rids[0], "Unknown")

            stats['least_active_trader'] = {
                'name': least_active_name,
                'count': min_count
            }

        if last_trade_time > 0:
            current_time = time.time() * 1000 # ms
            diff_ms = current_time - last_trade_time
            diff_days = diff_ms / (1000 * 3600 * 24)
            stats['days_since_last_trade'] = int(diff_days)

        return stats

    def get_trades_for_roster(self, roster_id):
        """Get all trades involving a specific roster."""
        trades = []
        for txn in self.transactions:
            if txn['type'] == 'trade' and roster_id in txn['roster_ids']:
                trades.append(txn)
        return sorted(trades, key=lambda x: x['created'], reverse=True)

    def build_trade_tree(self, root_transaction_id):
        """
        Builds a full directed graph (connected component) of transactions involving
        all assets in the root transaction. Traces both upstream (history) and downstream (future).
        """
        # Find root transaction
        root_txn = self.txn_map.get(root_transaction_id)
        if not root_txn:
            return None

        # Initialize graph
        G = nx.DiGraph()

        def get_txn_label(txn_data):
            if txn_data.get('type') == 'trade':
                return "Trade"
            return txn_data.get('type', 'Transaction').title()

        def add_txn_node(tid):
            if not G.has_node(tid):
                txn_data = self.txn_map.get(tid, {})
                label = get_txn_label(txn_data)
                G.add_node(tid, label=label, data=txn_data)

        # 1. Identify all assets (players) in the root transaction
        adds = root_txn.get('adds') or {}
        drops = root_txn.get('drops') or {}
        involved_assets = set(adds.keys()) | set(drops.keys())

        # 2. For each asset, get its full path and add to graph
        for asset_id in involved_assets:
            path = self.get_player_path(asset_id)
            asset_name = self.get_player_name(asset_id)

            # Path is a list of events ordered by date
            # Each event has a transaction_id

            previous_txn_id = None

            for event in path:
                current_txn_id = event['transaction_id']

                # Add node
                add_txn_node(current_txn_id)

                # If we have a previous transaction, add an edge
                if previous_txn_id:
                     # Check if edge already exists
                    if G.has_edge(previous_txn_id, current_txn_id):
                        # Append to label if not already there
                        current_label = G[previous_txn_id][current_txn_id].get('label', '')
                        if asset_name not in current_label:
                            G[previous_txn_id][current_txn_id]['label'] = f"{current_label}, {asset_name}"
                    else:
                        G.add_edge(previous_txn_id, current_txn_id, label=asset_name)

                previous_txn_id = current_txn_id

        return G
