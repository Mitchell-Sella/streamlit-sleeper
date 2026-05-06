import streamlit as st
import pandas as pd
import io
import math
import re

def get_tier_value(tier):
    tier_values = {
        1: 3000,
        2: 2000,
        3: 1400,
        4: 1000,
        5: 800,
        6: 550,
        7: 400,
        8: 150,
        9: 50,
        10: 20,
        11: 0
    }
    try:
        t = float(tier)
        if t <= 1: return tier_values[1]
        if t >= 11: return tier_values[11]

        lower_tier = int(math.floor(t))
        upper_tier = lower_tier + 1

        val_lower = tier_values[lower_tier]
        val_upper = tier_values.get(upper_tier, 0)

        fraction = t - lower_tier
        return val_lower - fraction * (val_lower - val_upper)
    except Exception:
        return 0

def clean_name(name):
    return re.sub(r'[^a-z0-9]', '', str(name).lower())

def process_uploaded_file(uploaded_file, analyzer):
    try:
        # Assuming tab separated or CSV
        content = uploaded_file.getvalue().decode("utf-8")
        if '\t' in content:
            df = pd.read_csv(io.StringIO(content), sep='\t')
        else:
            df = pd.read_csv(io.StringIO(content))

        # Ensure we have Player and AVGTier/Tier columns
        player_col = next((col for col in df.columns if col.lower() == 'player'), None)
        tier_col = next((col for col in df.columns if col.lower() in ['avgtier', 'tier']), None)

        if not player_col or not tier_col:
            st.error("Uploaded file must contain 'Player' and 'AVGTier' (or 'Tier') columns.")
            return None

        # Build player name matching mapping from analyzer
        player_name_to_id = {}
        for pid, p in analyzer.all_players.items():
            if p.get('position') in ['QB', 'RB', 'WR', 'TE']:
                fname = p.get('first_name', '')
                lname = p.get('last_name', '')
                search_name = p.get('search_full_name', '')

                # Using cleaned names
                cleaned_full = clean_name(f"{fname} {lname}")
                if cleaned_full:
                    player_name_to_id[cleaned_full] = pid

                cleaned_search = clean_name(search_name)
                if cleaned_search:
                    player_name_to_id[cleaned_search] = pid

        # Parse data
        parsed_data = {}
        for _, row in df.iterrows():
            player_name = str(row[player_col])
            tier_val = row[tier_col]
            value = get_tier_value(tier_val)

            c_name = clean_name(player_name)
            pid = player_name_to_id.get(c_name)

            if pid:
                parsed_data[pid] = {
                    'name': player_name,
                    'tier': tier_val,
                    'value': value,
                    'position': row.get('POS', analyzer.all_players[pid].get('position'))
                }
        return parsed_data
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None

# Page Config and Session Check
try:
    if 'analyzer' not in st.session_state or not st.session_state.analyzer:
        st.info("Please load league data in the sidebar.")
        st.stop()
    analyzer = st.session_state.analyzer
except Exception:
    # Handle pytest environment where st.session_state might raise error
    analyzer = None

st.title("Trade Finder")
st.markdown("Upload your custom player rankings/tiers to find advantageous trades.")

uploaded_file = st.file_uploader("Upload CSV/TSV Rankings", type=["csv", "tsv", "txt"])

if uploaded_file is not None:
    parsed_rankings = process_uploaded_file(uploaded_file, analyzer)

    if parsed_rankings:
        st.success(f"Successfully loaded rankings for {len(parsed_rankings)} players!")
        st.session_state.custom_rankings = parsed_rankings

        # Display sample
        sample_df = pd.DataFrame(list(parsed_rankings.values())).head()
        st.write("Sample parsed data:")
        st.dataframe(sample_df)

def compute_roster_strengths(parsed_rankings, analyzer):
    roster_strengths = {}

    for roster in analyzer.rosters:
        roster_id = roster['roster_id']
        owner_id = roster.get('owner_id')
        owner_name = analyzer.user_name_map.get(owner_id, f"Roster {roster_id}")

        pos_values = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0}
        players_data = []

        for pid in roster.get('players', []):
            if pid in parsed_rankings:
                p_data = parsed_rankings[pid]
                pos = p_data['position']
                val = p_data['value']

                if pos in pos_values:
                    pos_values[pos] += val

                players_data.append({
                    'player_id': pid,
                    'name': p_data['name'],
                    'position': pos,
                    'value': val,
                    'tier': p_data['tier']
                })

        roster_strengths[roster_id] = {
            'owner_name': owner_name,
            'pos_values': pos_values,
            'players': sorted(players_data, key=lambda x: x['value'], reverse=True)
        }

    return roster_strengths

def get_league_averages(roster_strengths):
    num_rosters = len(roster_strengths)
    if num_rosters == 0:
        return {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0}

    totals = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0}
    for rs in roster_strengths.values():
        for pos in totals:
            totals[pos] += rs['pos_values'][pos]

    return {pos: val / num_rosters for pos, val in totals.items()}

if 'custom_rankings' in st.session_state:
    parsed_rankings = st.session_state.custom_rankings
    roster_strengths = compute_roster_strengths(parsed_rankings, analyzer)
    league_averages = get_league_averages(roster_strengths)

    st.subheader("Team Strengths Analysis")

    # Let user select their team
    team_options = {rs['owner_name']: rid for rid, rs in roster_strengths.items()}

    default_team_index = 0
    if st.session_state.get('user'):
        current_name = st.session_state.user.get('display_name')
        if current_name in team_options:
            default_team_index = list(team_options.keys()).index(current_name)

    selected_team_name = st.selectbox("Select Your Team", options=list(team_options.keys()), index=default_team_index)
    selected_roster_id = team_options[selected_team_name]

    selected_team_data = roster_strengths[selected_roster_id]

    # Show strengths vs average
    strengths_df = pd.DataFrame([
        {'Position': pos, 'Your Value': selected_team_data['pos_values'][pos], 'League Avg': league_averages[pos], 'Difference': selected_team_data['pos_values'][pos] - league_averages[pos]}
        for pos in ['QB', 'RB', 'WR', 'TE']
    ])

    st.dataframe(strengths_df.style.map(lambda x: 'color: green' if x > 0 else ('color: red' if x < 0 else ''), subset=['Difference']))

import itertools

def generate_trades(my_roster, other_roster, my_strengths, my_weaknesses):
    """
    Generate trade combinations where:
    - I give players from my strengths
    - I receive players from my weaknesses
    """
    my_players = [p for p in my_roster['players'] if p['position'] in my_strengths]
    other_players = [p for p in other_roster['players'] if p['position'] in my_weaknesses]

    trades = []

    # 1 for 1
    for mp in my_players:
        for op in other_players:
            trades.append({
                'give': [mp],
                'receive': [op],
                'give_val': mp['value'],
                'receive_val': op['value']
            })

    # 2 for 1
    for mp1, mp2 in itertools.combinations(my_players, 2):
        for op in other_players:
            trades.append({
                'give': [mp1, mp2],
                'receive': [op],
                'give_val': mp1['value'] + mp2['value'],
                'receive_val': op['value']
            })

    # 1 for 2
    for mp in my_players:
        for op1, op2 in itertools.combinations(other_players, 2):
            trades.append({
                'give': [mp],
                'receive': [op1, op2],
                'give_val': mp['value'],
                'receive_val': op1['value'] + op2['value']
            })

    # Filter fair trades
    fair_trades = []
    for t in trades:
        # Ignore trades involving worthless players
        if t['give_val'] <= 0 or t['receive_val'] <= 0:
            continue

        diff = abs(t['give_val'] - t['receive_val'])
        avg_val = (t['give_val'] + t['receive_val']) / 2

        # Consider fair if within 15% diff
        if diff <= 0.15 * avg_val:
            # Also consider it "advantageous" if we gain value, or just show all fair ones.
            # Let's keep all fair ones and sort by net gain
            t['net'] = t['receive_val'] - t['give_val']
            fair_trades.append(t)

    return sorted(fair_trades, key=lambda x: x['net'], reverse=True)


if 'custom_rankings' in st.session_state:
    st.divider()
    st.subheader("Trade Ideas")

    # Determine strengths and weaknesses
    diffs = {pos: selected_team_data['pos_values'][pos] - league_averages[pos] for pos in ['QB', 'RB', 'WR', 'TE']}

    # Sort positions by difference
    sorted_pos = sorted(diffs.items(), key=lambda x: x[1])

    my_weaknesses = [sorted_pos[0][0], sorted_pos[1][0]] # Bottom 2
    my_strengths = [sorted_pos[2][0], sorted_pos[3][0]]  # Top 2

    st.write(f"**Seeking:** {', '.join(my_weaknesses)} | **Trading Away:** {', '.join(my_strengths)}")

    if st.button("Find Trades"):
        with st.spinner("Generating trade ideas..."):
            all_trades = []

            for other_rid, other_rdata in roster_strengths.items():
                if other_rid == selected_roster_id:
                    continue

                trades = generate_trades(selected_team_data, other_rdata, my_strengths, my_weaknesses)
                for t in trades:
                    t['partner'] = other_rdata['owner_name']
                    all_trades.append(t)

            all_trades = sorted(all_trades, key=lambda x: x['net'], reverse=True)

            if not all_trades:
                st.info("No fair trades found matching criteria.")
            else:
                st.success(f"Found {len(all_trades)} potential fair trades!")

                # Show top 50 trades
                for i, t in enumerate(all_trades[:50]):
                    give_names = ", ".join([f"{p['name']} ({p['position']})" for p in t['give']])
                    receive_names = ", ".join([f"{p['name']} ({p['position']})" for p in t['receive']])

                    with st.expander(f"Trade with {t['partner']}: Give {len(t['give'])} for {len(t['receive'])}"):
                        st.write(f"**Give:** {give_names} (Value: {t['give_val']})")
                        st.write(f"**Receive:** {receive_names} (Value: {t['receive_val']})")
                        st.write(f"**Net Value Change:** {t['net']:.1f}")
