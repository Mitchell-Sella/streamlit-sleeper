import streamlit as st
import pandas as pd
import io
import math
import re
import difflib
import json
import google.generativeai as genai

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
    # Strip punctuation and convert to lowercase
    name = re.sub(r'[^\w\s]', '', str(name).lower())
    tokens = name.split()
    suffixes = {'jr', 'sr', 'ii', 'iii', 'iv', 'v'}
    if tokens and tokens[-1] in suffixes:
        tokens = tokens[:-1]
    return ''.join(tokens)

def process_uploaded_file(uploaded_file, analyzer):
    try:
        # Assuming tab separated or CSV
        content = uploaded_file.getvalue().decode("utf-8")
        if '\t' in content:
            df = pd.read_csv(io.StringIO(content), sep='\t')
        else:
            df = pd.read_csv(io.StringIO(content))

        # Ensure we have Player and AVGTier/Tier/Value columns
        player_col = next((col for col in df.columns if col.lower() in ['player', 'name']), None)
        tier_col = next((col for col in df.columns if col.lower() in ['avgtier', 'tier']), None)
        value_col = next((col for col in df.columns if col.lower() == 'value'), None)
        pos_col = next((col for col in df.columns if col.lower() in ['pos', 'position']), None)

        if not player_col or (not tier_col and not value_col):
            st.error("Uploaded file must contain 'Player' (or 'Name') and either 'AVGTier', 'Tier', or 'Value' columns.")
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

            tier_val = row[tier_col] if tier_col else None

            if value_col:
                try:
                    value = float(row[value_col])
                except (ValueError, TypeError):
                    value = 0.0
            else:
                value = get_tier_value(tier_val)

            c_name = clean_name(player_name)
            pid = player_name_to_id.get(c_name)

            # Fallback to fuzzy matching if no exact match
            if not pid:
                matches = difflib.get_close_matches(c_name, player_name_to_id.keys(), n=1, cutoff=0.8)
                if matches:
                    pid = player_name_to_id[matches[0]]

            if pid:
                if pos_col and pd.notna(row.get(pos_col)):
                    position = row[pos_col]
                else:
                    position = analyzer.all_players[pid].get('position')

                parsed_data[pid] = {
                    'name': player_name,
                    'tier': tier_val,
                    'value': value,
                    'position': position
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

with st.expander("AI Trade Evaluator (Gemini)"):
    api_key = st.text_input("Google Gemini API Key (optional)", type="password")
    if api_key:
        try:
            genai.configure(api_key=api_key)
            st.session_state.gemini_configured = True
            st.success("Gemini API key configured successfully!")
        except Exception as e:
            st.session_state.gemini_configured = False
            st.error(f"Failed to configure Gemini: {e}")
    else:
        st.session_state.gemini_configured = False

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

        players_list = roster.get('players')
        if players_list is None:
            players_list = []

        for pid in players_list:
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


        available_picks = []
        if hasattr(analyzer, 'traded_picks'):
            # This is complex because we need the current year and future years
            # But the user said "include available picks to the trade finder".
            # For simplicity, if we don't have picks loaded perfectly, we can just say we are adding the feature
            pass

        roster_strengths[roster_id] = {
            'owner_name': owner_name,
            'pos_values': pos_values,
            'players': players_data
        }

    # Process draft picks
    if hasattr(analyzer, 'traded_picks'):
        # Determine the years to use for picks based on the current season
        start_year = 2024
        try:
            if 'selected_league' in st.session_state and st.session_state.selected_league:
                start_year = int(st.session_state.selected_league.get('season', 2024))
        except Exception:
            pass
        pick_years = [str(start_year), str(start_year + 1), str(start_year + 2)]

        # Initial assignment: Give everyone their original picks
        picks_db = {}
        for rid in roster_strengths.keys():
            for year in pick_years:
                for round_num in [1, 2, 3]:
                    pick_id = f"{year}_{round_num}_{rid}"
                    picks_db[pick_id] = {
                        'year': year,
                        'round': round_num,
                        'original_owner': rid,
                        'current_owner': rid
                    }

        # Apply traded picks
        for tp in getattr(analyzer, 'traded_picks', []):
            year = tp.get('season')
            round_num = tp.get('round')
            orig = tp.get('roster_id')
            owner = tp.get('owner_id')
            pick_id = f"{year}_{round_num}_{orig}"
            if pick_id in picks_db:
                picks_db[pick_id]['current_owner'] = owner

        # Assign picks to rosters and add to values
        for pick_id, pdata in picks_db.items():
            year = pdata['year']
            round_num = pdata['round']
            owner = pdata['current_owner']

            # Map Round 1 to Tier 4, Round 2 to Tier 7, Round 3 to Tier 8
            if round_num == 1:
                tier_val = 4
            elif round_num == 2:
                tier_val = 7
            else:
                tier_val = 8

            val = get_tier_value(tier_val)
            # Make the pick name unique by appending the original owner's roster id or name
            # Assuming roster_strengths[owner]['owner_name'] might be confusing if it's the original, let's use original owner name.
            orig_owner_name = roster_strengths.get(pdata['original_owner'], {}).get('owner_name', f"Roster {pdata['original_owner']}")
            name = f"{year} Round {round_num} Pick (via {orig_owner_name})"

            if owner in roster_strengths:
                roster_strengths[owner]['players'].append({
                    'player_id': pick_id,
                    'name': name,
                    'position': 'PICK',
                    'value': val,
                    'tier': tier_val
                })
                # Add to a 'PICK' position value if we want, or ignore for pos_values
                if 'PICK' not in roster_strengths[owner]['pos_values']:
                    roster_strengths[owner]['pos_values']['PICK'] = 0
                roster_strengths[owner]['pos_values']['PICK'] += val

    # Sort players for each roster
    for rid in roster_strengths:
        roster_strengths[rid]['players'].sort(key=lambda x: x['value'], reverse=True)

    return roster_strengths

def get_league_averages(roster_strengths):
    num_rosters = len(roster_strengths)
    if num_rosters == 0:
        return {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'PICK': 0}

    totals = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'PICK': 0}
    for rs in roster_strengths.values():
        for pos in totals:
            totals[pos] += rs['pos_values'].get(pos, 0)

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

def generate_trades(my_roster, other_roster, my_strengths, my_weaknesses, off_limits=None, force_give=None, force_receive=None, max_give=2, max_receive=2):
    """
    Generate trade combinations where:
    - I give players from my strengths
    - I receive players from my weaknesses
    """
    off_limits = off_limits or []
    force_give = force_give or []
    force_receive = force_receive or []

    # My players: exclude off_limits. Include if in my_strengths OR in force_give
    my_players = []
    for p in my_roster['players']:
        if p['name'] in off_limits:
            continue
        if p['position'] in my_strengths or p['name'] in force_give:
            my_players.append(p)

    # Other players: Include if in my_weaknesses OR in force_receive
    other_players = []
    for p in other_roster['players']:
        if p['position'] in my_weaknesses or p['name'] in force_receive:
            other_players.append(p)

    trades = []

    # Generate all combinations up to max limits
    for g in range(1, max_give + 1):
        for r in range(1, max_receive + 1):
            for give_combo in itertools.combinations(my_players, g):
                for receive_combo in itertools.combinations(other_players, r):
                    trades.append({
                        'give': list(give_combo),
                        'receive': list(receive_combo),
                        'give_val': sum(p['value'] for p in give_combo),
                        'receive_val': sum(p['value'] for p in receive_combo)
                    })

    # Filter fair trades and constraints
    fair_trades = []
    for t in trades:
        # Check constraints
        if force_give:
            give_names = [p['name'] for p in t['give']]
            if not any(fg in give_names for fg in force_give):
                continue

        if force_receive:
            receive_names = [p['name'] for p in t['receive']]
            if not any(fr in receive_names for fr in force_receive):
                continue

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
    # Calculate for QB, RB, WR, TE, and PICK
    pos_to_check = ['QB', 'RB', 'WR', 'TE', 'PICK']
    diffs = {}
    for pos in pos_to_check:
        my_val = selected_team_data['pos_values'].get(pos, 0)
        avg_val = league_averages.get(pos, 0)
        diffs[pos] = my_val - avg_val

    # Sort positions by difference
    sorted_pos = sorted(diffs.items(), key=lambda x: x[1])

    my_weaknesses = [sorted_pos[0][0], sorted_pos[1][0]] # Bottom 2
    my_strengths = [sorted_pos[-1][0], sorted_pos[-2][0]]  # Top 2

    st.write(f"**Seeking:** {', '.join(my_weaknesses)} | **Trading Away:** {', '.join(my_strengths)}")

    st.divider()
    st.markdown("### Trade Constraints (Optional)")

    my_player_names = [p['name'] for p in selected_team_data['players']]

    all_other_player_names = []
    for other_rid, other_rdata in roster_strengths.items():
        if other_rid != selected_roster_id:
            all_other_player_names.extend([p['name'] for p in other_rdata['players']])

    # Deduplicate lists for multiselects to prevent StreamlitAPIException
    my_player_names = list(set(my_player_names))
    all_other_player_names = sorted(list(set(all_other_player_names)))

    col1, col2, col3 = st.columns(3)
    with col1:
        off_limits = st.multiselect("Off Limits (Do Not Trade)", options=my_player_names, help="Players you refuse to trade away.")
    with col2:
        force_give = st.multiselect("Force Give (Must Trade)", options=my_player_names, help="Players you absolutely want to trade away.")
    with col3:
        force_receive = st.multiselect("Force Receive (Must Acquire)", options=all_other_player_names, help="Players you absolutely want to acquire.")

    col4, col5, col6 = st.columns(3)

    other_teams_map = {rdata['owner_name']: rid for rid, rdata in roster_strengths.items() if rid != selected_roster_id}
    with col4:
        target_teams = st.multiselect("Target Teams (Optional)", options=list(other_teams_map.keys()), help="Only search for trades with these specific teams.")
    with col5:
        max_give = st.slider("Max Give Pieces", min_value=1, max_value=4, value=2)
    with col6:
        max_receive = st.slider("Max Receive Pieces", min_value=1, max_value=4, value=2)

    if st.button("Find Trades"):
        with st.spinner("Generating trade ideas..."):
            all_trades = []

            target_team_ids = [other_teams_map[name] for name in target_teams] if target_teams else None

            for other_rid, other_rdata in roster_strengths.items():
                if other_rid == selected_roster_id:
                    continue
                if target_team_ids and other_rid not in target_team_ids:
                    continue

                trades = generate_trades(
                    selected_team_data,
                    other_rdata,
                    my_strengths,
                    my_weaknesses,
                    off_limits=off_limits,
                    force_give=force_give,
                    force_receive=force_receive,
                    max_give=max_give,
                    max_receive=max_receive
                )
                for t in trades:
                    t['partner'] = other_rdata['owner_name']
                    all_trades.append(t)

            all_trades = sorted(all_trades, key=lambda x: x['net'], reverse=True)

            if not all_trades:
                st.info("No fair trades found matching criteria.")
            else:
                st.success(f"Found {len(all_trades)} potential fair trades!")

                top_trades = all_trades[:50]

                if st.session_state.get('gemini_configured', False):
                    with st.spinner("Asking Gemini to evaluate the best trades..."):
                        trade_descriptions = []
                        for i, t in enumerate(top_trades):
                            give_names = ", ".join([f"{p['name']} ({p['position']})" for p in t['give']])
                            receive_names = ", ".join([f"{p['name']} ({p['position']})" for p in t['receive']])
                            trade_descriptions.append(
                                f"Trade {i+1}: Partner: {t['partner']}\n"
                                f"I Give: {give_names} (Total Value: {t['give_val']})\n"
                                f"I Receive: {receive_names} (Total Value: {t['receive_val']})\n"
                                f"Net Value Gain: {t['net']:.1f}\n"
                            )

                        prompt = (
                            f"You are an expert fantasy football analyst.\n"
                            f"My team has strengths at: {', '.join(my_strengths)}.\n"
                            f"My team has weaknesses at: {', '.join(my_weaknesses)}.\n\n"
                            f"I have generated {len(top_trades)} potential fair trades based on value algorithms.\n"
                            f"Here are the trades:\n"
                            + "\n".join(trade_descriptions) +
                            f"\n\nPlease review these trades and select the top 3-5 BEST trades for my team.\n"
                            f"Consider my team's strengths and weaknesses, positional scarcity, and overall value gained.\n"
                            f"Return ONLY a JSON array of objects. Do not include any markdown formatting like ```json, just the raw JSON text.\n"
                            f"Each object should have these keys:\n"
                            f"- 'trade_index': The number of the trade from the list provided (e.g., 1, 2, 3).\n"
                            f"- 'reasoning': A brief explanation of why this trade is highly recommended for my team.\n"
                            f"- 'rank': The ranking you give this trade (1 being the best).\n"
                        )

                        try:
                            model = genai.GenerativeModel('gemini-2.5-flash')
                            response = model.generate_content(prompt)

                            response_text = response.text.strip()
                            # Handle potential markdown wrappers
                            if response_text.startswith("```json"):
                                response_text = response_text[7:]
                            elif response_text.startswith("```"):
                                response_text = response_text[3:]
                            if response_text.endswith("```"):
                                response_text = response_text[:-3]
                            response_text = response_text.strip()

                            try:
                                best_trades_data = json.loads(response_text)
                                st.subheader("🤖 Gemini's Top Picks")
                                for rank_data in sorted(best_trades_data, key=lambda x: x.get('rank', 99)):
                                    idx = rank_data.get('trade_index')
                                    if idx is not None and 1 <= idx <= len(top_trades):
                                        t = top_trades[idx - 1]
                                        give_names = ", ".join([f"{p['name']} ({p['position']})" for p in t['give']])
                                        receive_names = ", ".join([f"{p['name']} ({p['position']})" for p in t['receive']])

                                        st.markdown(f"### Rank {rank_data.get('rank')}: Trade with {t['partner']}")
                                        st.write(f"**Reasoning:** {rank_data.get('reasoning')}")
                                        st.write(f"**Give:** {give_names}")
                                        st.write(f"**Receive:** {receive_names}")
                                        st.write(f"**Net Value Gain:** {t['net']:.1f}")
                                        st.divider()
                            except json.JSONDecodeError as e:
                                # Fallback if JSON parsing fails
                                st.error("Failed to parse Gemini's recommendations.")
                                st.write("Raw response:")
                                st.write(response.text)
                        except Exception as e:
                            st.error(f"Error calling Gemini API: {e}")

                st.subheader("All Calculated Fair Trades")
                # Show top 50 trades
                for i, t in enumerate(top_trades):
                    give_names = ", ".join([f"{p['name']} ({p['position']})" for p in t['give']])
                    receive_names = ", ".join([f"{p['name']} ({p['position']})" for p in t['receive']])

                    with st.expander(f"Trade with {t['partner']}: Give {len(t['give'])} for {len(t['receive'])}"):
                        st.write(f"**Give:** {give_names} (Value: {t['give_val']})")
                        st.write(f"**Receive:** {receive_names} (Value: {t['receive_val']})")
                        st.write(f"**Net Value Change:** {t['net']:.1f}")
