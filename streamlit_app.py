import streamlit as st
import pandas as pd
from services.sleeper import SleeperService
from services.analyzer import LeagueAnalyzer
from views import stats as stats_view

# Page config
st.set_page_config(
    page_title="League Trade Explorer",
    page_icon=":material/swap_horiz:",
    layout="wide"
)

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'leagues' not in st.session_state:
    st.session_state.leagues = []
if 'selected_league' not in st.session_state:
    st.session_state.selected_league = None
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = None
if 'league_history_map' not in st.session_state:
    st.session_state.league_history_map = {}

def load_data(selected_league_ids):
    """Fetch data for selected league IDs and initialize analyzer."""
    if st.session_state.selected_league and selected_league_ids:
        league_id = st.session_state.selected_league['league_id']

        with st.spinner(f"Fetching data for {len(selected_league_ids)} seasons..."):

            # 1. Fetch transactions for SELECTED leagues in history
            transactions = SleeperService.get_all_transactions(selected_league_ids)

            # 2. Fetch rosters & users (from current league mostly)
            # Use the most recent league ID (the selected one usually)
            # Actually, roster IDs are usually consistent across history in Dynasty?
            # Or do they change? They usually persist if it's the same league chain.
            # But users might change.
            rosters = SleeperService.get_rosters(league_id)
            users = SleeperService.get_users_in_league(league_id)

            # 3. Fetch players
            all_players = SleeperService.get_all_players()

            # 4. Fetch Draft Data
            draft_data = []
            progress_bar = st.progress(0)
            total_leagues = len(selected_league_ids)

            for i, lid in enumerate(selected_league_ids):
                # Update progress
                progress_bar.progress((i + 1) / total_leagues, text=f"Fetching drafts for season {i+1}...")

                drafts = SleeperService.get_drafts_in_league(lid)
                for draft in drafts:
                    d_id = draft['draft_id']
                    # We need full draft details for slot_to_roster_id mapping
                    full_draft = SleeperService.get_draft(d_id)
                    picks = SleeperService.get_draft_picks(d_id)

                    if full_draft:
                        draft_data.append({'draft': full_draft, 'picks': picks})

            progress_bar.empty()

            # Initialize Analyzer
            analyzer = LeagueAnalyzer(transactions, rosters, users, all_players)
            analyzer.initialize_drafts(draft_data)
            st.session_state.analyzer = analyzer

            st.success(f"Loaded data with {len(transactions)} transactions and {len(draft_data)} drafts!")

def load_user_data():
    """Callback to load user data when username changes."""
    # Reset state on user change
    st.session_state.selected_league = None
    st.session_state.analyzer = None
    st.session_state.league_history_map = {}

    username = st.session_state.username_input
    if username:
        user = SleeperService.get_user(username)
        if user:
            st.session_state.user = user
            # Fetch leagues - try recent years if 2024 fails
            found_leagues = []
            # Try a range of years to find active leagues
            # Prioritize 2025 to capture new draft data if available
            for year in ["2025", "2024", "2023"]:
                leagues = SleeperService.get_all_leagues(user['user_id'], season=year)
                if leagues:
                    found_leagues = leagues
                    break

            st.session_state.leagues = found_leagues
            if not found_leagues:
                st.warning("No recent leagues found (2023-2025).")
        else:
            st.error("User not found.")
            st.session_state.user = None
            st.session_state.leagues = []

# Sidebar
with st.sidebar:
    st.title("Sleeper Streamlit")

    st.text_input("Sleeper Username", key="username_input", on_change=load_user_data)

    if st.session_state.user:
        st.write(f"Logged in as: **{st.session_state.user['display_name']}**")

        league_options = {l['name']: l for l in st.session_state.leagues}
        if league_options:
            # Helper to format league name in selectbox
            def format_league_name(l_name):
                return l_name

            selected_league_name = st.selectbox("Select League", options=list(league_options.keys()))

            if selected_league_name:
                selected_league = league_options[selected_league_name]

                # Check if selection changed
                if st.session_state.selected_league != selected_league:
                    st.session_state.selected_league = selected_league
                    st.session_state.analyzer = None # Reset analyzer
                    st.session_state.league_history_map = {} # Reset history

                # Fetch history map if not already done for this league
                if not st.session_state.league_history_map:
                    with st.spinner("Finding league history..."):
                        history_ids = SleeperService.get_league_history(selected_league['league_id'])
                        history_map = {}
                        for lid in history_ids:
                            l_data = SleeperService.get_league(lid)
                            if l_data:
                                history_map[l_data['season']] = lid
                        st.session_state.league_history_map = history_map

                # Automatically load all history
                if st.button("Analyze League History"):
                    # Use all available history IDs
                    if st.session_state.league_history_map:
                        selected_ids = list(st.session_state.league_history_map.values())
                        load_data(selected_ids)
                    else:
                        st.error("Could not fetch league history.")
        else:
            st.warning("No leagues found.")

# Main Area
if st.session_state.analyzer:
    stats_view.show(st.session_state.analyzer)
else:
    st.info("Please enter your Sleeper username and select a league to begin.")
