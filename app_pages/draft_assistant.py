import streamlit as st
import pandas as pd
from services.sleeper import SleeperService
from utils import clean_name

if 'analyzer' not in st.session_state or not st.session_state.analyzer:
    st.info("Please load league data in the sidebar.")
    st.stop()

analyzer = st.session_state.analyzer
league = st.session_state.selected_league

st.title("Draft Assistant")

# Select Draft
drafts = SleeperService.get_drafts_in_league(league['league_id'])
if not drafts:
    st.warning("No drafts found for this league.")
    st.stop()

# Let user pick draft
draft_options = {f"{d['season']} - {d['status']}": d for d in drafts}
selected_draft_label = st.selectbox("Select Draft", options=list(draft_options.keys()))
selected_draft = draft_options[selected_draft_label]

st.divider()

# File Uploader
uploaded_file = st.file_uploader("Upload Rankings CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]

    # We expect 'player', 'position', 'rank', 'tier'
    # Fallback to 'full_name' for player if needed
    player_col = 'player' if 'player' in df.columns else 'full_name' if 'full_name' in df.columns else None

    if not player_col:
        st.error("CSV must contain a 'Player' or 'full_name' column.")
        st.stop()

    # Map player names to IDs
    name_to_id = {}
    for pid, pdata in analyzer.all_players.items():
        if isinstance(pdata, dict):
            fname = pdata.get('full_name')
            if not fname:
                fname = f"{pdata.get('first_name', '')} {pdata.get('last_name', '')}".strip()
            if fname:
                name_to_id[clean_name(fname)] = pid

    def get_id(row):
        if 'player_id' in row and pd.notna(row['player_id']):
            return str(row['player_id'])
        name = row[player_col]
        return name_to_id.get(clean_name(name))

    df['player_id'] = df.apply(get_id, axis=1)

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Refresh Draft Picks"):
            SleeperService.get_draft_picks.clear()
            SleeperService.get_drafts_in_league.clear()
            SleeperService.get_draft.clear()
            st.rerun()

    # using get_draft_picks which fetches all picks including live ones for active drafts
    picks = SleeperService.get_draft_picks(selected_draft['draft_id'])
    drafted_ids = set([str(p['player_id']) for p in picks if p.get('player_id')])

    # Determine user's upcoming picks
    user_id = st.session_state.user['user_id']
    draft_order = selected_draft.get('draft_order')
    user_slot = None
    if draft_order and user_id in draft_order:
        user_slot = draft_order[user_id]
    elif selected_draft.get('slot_to_roster_id'):
        # Fallback to roster ID
        rosters = SleeperService.get_rosters(selected_draft['league_id'])
        user_roster = next((r for r in rosters if r.get('owner_id') == user_id), None)
        if user_roster:
            roster_id = user_roster['roster_id']
            for slot_str, r_id in selected_draft['slot_to_roster_id'].items():
                if r_id == roster_id:
                    user_slot = int(slot_str)
                    break

    settings = selected_draft.get('settings', {})
    teams = settings.get('teams', 10)
    rounds = settings.get('rounds', 15)
    reversal_round = settings.get('reversal_round', 0)
    draft_type = selected_draft.get('type', 'snake')

    user_picks = []
    if user_slot:
        current_pick_no = len(picks) + 1
        for r in range(1, rounds + 1):
            if draft_type == 'snake':
                is_forward = (r % 2 != 0)
                if reversal_round > 0 and r >= reversal_round:
                    is_forward = not is_forward

                if is_forward:
                    pick = (r - 1) * teams + user_slot
                else:
                    pick = (r - 1) * teams + (teams - user_slot + 1)
            else:
                # Linear draft
                pick = (r - 1) * teams + user_slot

            if pick >= current_pick_no:
                user_picks.append(pick)

        if user_picks:
            next_pick = user_picks[0]
            st.info(f"Your next pick: **{next_pick}**. Upcoming picks: {', '.join([str(p) for p in user_picks[:5]])}")
            st.caption(f"Based on your upcoming picks, look for players ranked around {next_pick}.")
        else:
            st.info("You have no more picks in this draft.")
    else:
        st.info("Could not determine your draft slot. You might not be participating in this draft.")

    unmapped = df[df['player_id'].isna()]
    if not unmapped.empty:
        st.warning(f"Could not map {len(unmapped)} players to Sleeper IDs. They might not show correctly if drafted.")

    # Add a status column for color coding
    df['Status'] = df['player_id'].apply(lambda x: 'Drafted' if str(x) in drafted_ids else 'Available')

    # We can use pandas styling to highlight available players
    def highlight_status(val):
        color = 'lightgreen' if val == 'Available' else 'lightgray'
        return f'background-color: {color}'

    st.subheader("Players By Tier")

    if 'tier' in df.columns:
        tiers = df['tier'].dropna().unique()
        tiers = sorted(tiers)
        for t in tiers:
            st.markdown(f"### Tier {t}")
            tier_df = df[df['tier'] == t]

            # sort by rank if possible
            if 'rank' in tier_df.columns:
                tier_df = tier_df.sort_values(by='rank')

            cols_to_show = [player_col]
            if 'position' in tier_df.columns: cols_to_show.append('position')
            if 'rank' in tier_df.columns: cols_to_show.append('rank')
            cols_to_show.append('Status')

            styled_df = tier_df[cols_to_show].style.map(highlight_status, subset=['Status'])
            st.dataframe(styled_df, hide_index=True, use_container_width=True)
    else:
        # If no tier column, just show the whole thing
        if 'rank' in df.columns:
            df = df.sort_values(by='rank')

        cols_to_show = [player_col]
        if 'position' in df.columns: cols_to_show.append('position')
        if 'rank' in df.columns: cols_to_show.append('rank')
        cols_to_show.append('Status')

        styled_df = df[cols_to_show].style.map(highlight_status, subset=['Status'])
        st.dataframe(styled_df, hide_index=True, use_container_width=True)
