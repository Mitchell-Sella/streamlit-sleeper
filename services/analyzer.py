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

        # Map (season, round, original_roster_id) -> {'player': player_name, 'label': pick_label}
        self.pick_map = {}

    def initialize_drafts(self, draft_data):
        """
        Ingests draft data to resolve traded picks to players.
        draft_data: List of {'draft': draft_object, 'picks': [pick_objects]}
        """
        for entry in draft_data:
            draft = entry['draft']
            picks = entry['picks']

            season = draft.get('season')
            slot_to_roster = draft.get('slot_to_roster_id')

            if not season or not slot_to_roster:
                continue

            # Create a map of slot -> roster_id (ensure types match)
            # slot keys are usually strings "1", "2". roster_ids are ints.
            # We need to map roster_id -> slot to find which column corresponds to which original owner.

            # Note: A roster might map to multiple slots? Unlikely in standard leagues.
            roster_to_slots = defaultdict(list)
            for slot, rid in slot_to_roster.items():
                roster_to_slots[rid].append(int(slot))

            # Group picks by round to calculate pick-in-round
            # Sort picks by overall pick number (or draft_slot if pick_no missing)
            sorted_picks = sorted(picks, key=lambda x: x.get('pick_no', x.get('draft_slot', 0)))

            round_counts = defaultdict(int)

            # Process picks
            for pick in sorted_picks:
                p_round = pick.get('round')
                p_slot = pick.get('draft_slot')
                player_id = pick.get('player_id')

                # Calculate pick in round (1-based index within the round)
                round_counts[p_round] += 1
                pick_in_round = round_counts[p_round]

                # Format label: "1.02"
                pick_label = f"{p_round}.{pick_in_round:02d}"

                if not player_id:
                    continue

                # Find which roster this slot belonged to originally
                # Invert logic: find roster_id where p_slot in their slots
                # (Slightly inefficient but N is small)

                original_roster_id = None
                for rid, slots in roster_to_slots.items():
                    if p_slot in slots:
                        original_roster_id = rid
                        break

                if original_roster_id:
                    key = (str(season), int(p_round), int(original_roster_id))
                    player_name = self.get_player_name(player_id)
                    self.pick_map[key] = {
                        'player': player_name,
                        'label': pick_label
                    }

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

    def get_trades_between(self, proposer, accepter):
        """
        Get list of trades between proposer (sender) and accepter (receiver).
        If proposer or accepter is None, it acts as a wildcard.

        'proposer' and 'accepter' are display names (strings).
        """
        trades = []

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

            # Determine Proposer and Accepters for this transaction

            # 1. Identify Proposer
            proposer_name = None
            accepter_names = []

            creator_id = txn.get('creator')
            proposer_rid = None

            if has_creator and creator_id:
                for rid in roster_ids:
                    if self.roster_owner_map.get(rid) == creator_id:
                        proposer_rid = rid
                        break

            if has_creator and proposer_rid:
                # Asymmetric
                proposer_name = self.roster_name_map.get(proposer_rid)

                for rid in roster_ids:
                    if rid == proposer_rid:
                        continue
                    accepter_names.append(self.roster_name_map.get(rid))

                # Check match
                # Case 1: Specific Proposer and Specific Accepter
                # Case 2: Wildcard Proposer (None) -> match if Accepter matches any in list
                # Case 3: Wildcard Accepter (None) -> match if Proposer matches

                match_proposer = (proposer is None) or (proposer == proposer_name)
                match_accepter = (accepter is None) or (accepter in accepter_names)

                if match_proposer and match_accepter:
                    trades.append(txn)

            else:
                # Symmetric (Fallback)
                # In symmetric mode, there is no distinct "Proposer".
                # Both parties are considered involved.
                # If Proposer="A" and Accepter="B", we look for trade involving A and B.
                # If Proposer="A" and Accepter=None, we look for trade involving A.

                participants = [self.roster_name_map.get(rid) for rid in roster_ids]

                has_p = (proposer is None) or (proposer in participants)
                has_a = (accepter is None) or (accepter in participants)

                if has_p and has_a:
                     trades.append(txn)

        return sorted(trades, key=lambda x: x['created'], reverse=True)

    def get_enriched_trades(self, trades, proposer_name, accepter_name):
        """
        Enriches a list of trade transactions with detailed asset information (players, picks)
        grouped by who received them (Proposer vs Accepter).

        Args:
            trades: List of trade transactions.
            proposer_name: Display name of the proposer (or wildcard).
            accepter_name: Display name of the accepter (or wildcard).

        Returns:
            List of dictionaries:
            {
                'date': timestamp,
                'transaction_id': str,
                'proposer': str,
                'accepter': str,
                'proposer_receives': [], # List of strings/dicts describing assets
                'accepter_receives': []
            }
        """
        enriched = []

        # Helper to get roster ID from name
        # We need reverse map: Name -> [Roster IDs] (since names might not be unique, but usually are)
        # But we only have roster_id -> name.
        # We can scan roster_name_map.

        for txn in trades:
            ts = txn['created']

            # Identify Proposer and Accepter Roster IDs for THIS transaction
            # (Since proposer_name might be None/Wildcard, or symmetric)

            roster_ids = txn.get('roster_ids', [])
            if len(roster_ids) < 2:
                continue

            # If we know the specific proposer/accepter names from args, find their IDs in this txn
            # If wildcard, we just pick the two participants (assuming 2-team trade for simplicity)

            # Current participants in this txn
            participants = {rid: self.roster_name_map.get(rid, f"Roster {rid}") for rid in roster_ids}

            # Determining "Proposer" vs "Accepter" for the display
            # If arguments provided specific names, use them to label the sides.
            # If not (e.g. Total vs Total), we can just pick one as "Side A" and one as "Side B"
            # However, typically 'creator' is the proposer.

            creator_id = txn.get('creator')
            proposer_rid = None
            if creator_id:
                for rid in roster_ids:
                    if self.roster_owner_map.get(rid) == creator_id:
                        proposer_rid = rid
                        break

            # If we can't identify creator, or it's not in roster_ids, just pick first as Proposer
            if not proposer_rid:
                proposer_rid = roster_ids[0]

            # The other is Accepter (assuming 2 teams)
            accepter_rid = None
            for rid in roster_ids:
                if rid != proposer_rid:
                    accepter_rid = rid
                    break

            if not accepter_rid:
                continue # Single team trade?

            p_name = self.roster_name_map.get(proposer_rid, f"Roster {proposer_rid}")
            a_name = self.roster_name_map.get(accepter_rid, f"Roster {accepter_rid}")

            # Assets
            p_receives = []
            a_receives = []

            # 1. Adds (Players received)
            adds = txn.get('adds') or {}
            for player_id, roster_id in adds.items():
                # roster_id is who received the player
                player_name = self.get_player_name(player_id)

                # REQ: Remove details (pos/team)
                asset_str = f"**{player_name}**"

                if roster_id == proposer_rid:
                    p_receives.append(asset_str)
                elif roster_id == accepter_rid:
                    a_receives.append(asset_str)

            # 2. Draft Picks
            picks = txn.get('draft_picks') or []
            for pick in picks:
                # pick: {season, round, roster_id (original owner), owner_id (new owner), ...}
                season = pick.get('season')
                round_num = pick.get('round')
                original_owner_rid = pick.get('roster_id')
                new_owner_rid = pick.get('owner_id')

                original_owner_name = self.roster_name_map.get(original_owner_rid, f"Roster {original_owner_rid}")

                # Check if resolved
                pick_key = (str(season), int(round_num), int(original_owner_rid))

                pick_str = ""

                if pick_key in self.pick_map:
                    # Pick has been made
                    pick_data = self.pick_map[pick_key]
                    label = pick_data['label']
                    player = pick_data['player']
                    # REQ: Use "1.02" format instead of "via..."
                    pick_str = f"**{season} {label}** (Selected: {player})"
                else:
                    # Pick is future or not resolved
                    # Format: 2026 Round 1 (Original: Name)
                    # Convert round to suffix (1st, 2nd, 3rd)
                    suffix = "th"
                    if 10 <= round_num % 100 <= 20:
                        suffix = "th"
                    else:
                        last = round_num % 10
                        if last == 1: suffix = "st"
                        elif last == 2: suffix = "nd"
                        elif last == 3: suffix = "rd"

                    pick_str = f"**{season} {round_num}{suffix} Rd** (via {original_owner_name})"

                if new_owner_rid == proposer_rid:
                    p_receives.append(pick_str)
                elif new_owner_rid == accepter_rid:
                    a_receives.append(pick_str)

            enriched.append({
                'date': ts,
                'transaction_id': txn['transaction_id'],
                'proposer': p_name,
                'accepter': a_name,
                'proposer_receives': p_receives,
                'accepter_receives': a_receives
            })

        return sorted(enriched, key=lambda x: x['date'], reverse=True)

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
