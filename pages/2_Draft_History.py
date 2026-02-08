import streamlit as st
import pandas as pd
import altair as alt
from collections import defaultdict

# --- Utility Functions ---

def get_drafters(draft_data, analyzer_instance):
    """Identify unique users who have made picks."""
    drafter_ids = set()
    for entry in draft_data:
        for pick in entry['picks']:
            picked_by = pick.get('picked_by')
            if picked_by:
                drafter_ids.add(picked_by)

    # Map to names
    user_map = {}
    for uid in drafter_ids:
        # Use analyzer's map (which might be from current league) or fallback
        # Accessing analyzer instance directly
        name = analyzer_instance.user_name_map.get(uid, f"User {uid}")
        user_map[name] = uid
    return user_map

def process_draft_history(draft_data, selected_user_id, analyzer_instance):
    """
    Process draft data to count picks per slot for a specific user
    and list players selected.
    """
    # Grid: (round, pick_in_round) -> count
    grid_counts = defaultdict(int)
    # List: [{'Season', 'Round', 'Pick', 'Slot', 'Player'}]
    player_history_list = []

    for entry in draft_data:
        draft = entry['draft']
        season = draft.get('season')
        picks = entry['picks']

        # Sort picks by pick_no or draft_slot
        sorted_picks = sorted(picks, key=lambda x: x.get('pick_no', x.get('draft_slot', 0)))

        # Track pick number within each round for THIS draft
        round_counters = defaultdict(int)

        for pick in sorted_picks:
            p_round = pick.get('round')

            # Increment counter for this round
            round_counters[p_round] += 1
            p_in_round = round_counters[p_round]

            # Check if picked by selected user
            if pick.get('picked_by') == selected_user_id:
                grid_counts[(p_round, p_in_round)] += 1

                pid = pick.get('player_id')
                # Use helper if available, else simple lookup
                p_name = analyzer_instance.get_player_name(pid)

                player_history_list.append({
                    'Season': season,
                    'Round': p_round,
                    'Pick': p_in_round,
                    'Slot': f"{p_round}.{p_in_round:02d}",
                    'Player': p_name
                })

    return grid_counts, player_history_list

# --- Page Logic ---

st.set_page_config(page_title="Draft History", page_icon=":material/grid_on:", layout="wide")

# Ensure data is loaded
if 'analyzer' not in st.session_state or not st.session_state.analyzer:
    st.info("Please load league data on the Home page first.")
    st.stop()

analyzer = st.session_state.analyzer
draft_data = st.session_state.get('draft_data', [])

st.title("Draft History")

# 1. User Selection
user_options_map = get_drafters(draft_data, analyzer)

if not user_options_map:
    st.warning("No draft data found with assigned users.")
    st.stop()

# Determine default selection based on logged-in user
default_index = 0
current_user_id = st.session_state.user.get('user_id') if st.session_state.user else None
# Find name for current user (if logged in and in the list)
current_user_name_found = None
if current_user_id:
    # Reverse lookup name or check map
    # Since keys are names, we need to find which key has value == current_user_id
    for name, uid in user_options_map.items():
        if uid == current_user_id:
            current_user_name_found = name
            break

if current_user_name_found:
    keys = list(user_options_map.keys())
    try:
        default_index = keys.index(current_user_name_found)
    except ValueError:
        pass

selected_user_name = st.selectbox("Select User", options=list(user_options_map.keys()), index=default_index)
selected_user_uid = user_options_map[selected_user_name]

st.divider()

# 2. Process Data
grid_counts_res, player_history_res = process_draft_history(draft_data, selected_user_uid, analyzer)

# 3. Visualization

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"Draft Grid: {selected_user_name}")

    if grid_counts_res:
        # Convert to DF for Altair
        heatmap_data = []
        for (r, p), count in grid_counts_res.items():
            heatmap_data.append({'Round': int(r), 'Pick': int(p), 'Count': int(count)})

        df_heatmap = pd.DataFrame(heatmap_data)

        # Create Heatmap
        base = alt.Chart(df_heatmap).encode(
            x=alt.X('Pick:O', title='Pick Number'),
            y=alt.Y('Round:O', title='Round'),
        )

        heatmap = base.mark_rect().encode(
            color=alt.Color('Count:Q', scale=alt.Scale(scheme='greens'), legend=None),
            tooltip=['Round', 'Pick', 'Count']
        )

        text = base.mark_text(baseline='middle').encode(
            text=alt.Text('Count:Q', format='d'),
            color=alt.value('black') # Simple black text
        )

        chart = (heatmap + text).properties(
            # width=600,
            # height=max_round * 40 + 50
        )

        st.altair_chart(chart, use_container_width=True)
        st.caption("Each cell represents a draft slot (Round.Pick). The number indicates how many times you selected from that slot.")

    else:
        st.info("No picks found for this user.")

with col2:
    st.subheader("Drafted Players")

    if player_history_res:
        df_players = pd.DataFrame(player_history_res)
        # Sort by Season desc
        df_players = df_players.sort_values(by=['Season', 'Round', 'Pick'], ascending=[False, True, True])

        st.dataframe(
            df_players[['Season', 'Slot', 'Player']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.write("No players selected.")
