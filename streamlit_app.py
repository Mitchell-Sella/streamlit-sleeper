import streamlit as st
import pandas as pd
from services.sleeper import SleeperService
from services.analyzer import LeagueAnalyzer

# Page config
st.set_page_config(
    page_title="Sleeper Network Explorer",
    page_icon="🏈",
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

            # 2. Fetch rosters & users (from current league mostly)
            rosters = SleeperService.get_rosters(league_id)
            users = SleeperService.get_users_in_league(league_id)

            # 3. Fetch transactions for SELECTED leagues in history
            transactions = SleeperService.get_all_transactions(selected_league_ids)

            # 4. Fetch players
            all_players = SleeperService.get_all_players()

            # Initialize Analyzer
            st.session_state.analyzer = LeagueAnalyzer(transactions, rosters, users, all_players)
            st.success(f"Loaded data with {len(transactions)} transactions!")

def load_user_data():
    """Callback to load user data when username changes."""
    username = st.session_state.username_input
    if username:
        user = SleeperService.get_user(username)
        if user:
            st.session_state.user = user
            # Fetch leagues - try recent years if 2024 fails
            found_leagues = []
            for year in ["2025", "2024", "2023", "2022"]:
                leagues = SleeperService.get_all_leagues(user['user_id'], season=year)
                if leagues:
                    found_leagues = leagues
                    break

            st.session_state.leagues = found_leagues
            if not found_leagues:
                st.warning("No recent leagues found (2022-2025).")
        else:
            st.error("User not found.")
            st.session_state.user = None
            st.session_state.leagues = []

# Sidebar
with st.sidebar:
    st.title("Sleeper Network")

    st.text_input("Sleeper Username", key="username_input", on_change=load_user_data)

    if st.session_state.user:
        st.write(f"Logged in as: **{st.session_state.user['display_name']}**")

        league_options = {l['name']: l for l in st.session_state.leagues}
        if league_options:
            selected_league_name = st.selectbox("Select League", options=list(league_options.keys()))

            if selected_league_name:
                selected_league = league_options[selected_league_name]
                st.session_state.selected_league = selected_league

                # Fetch history map if not already done for this league
                # (Or refresh it every time to be safe)
                with st.spinner("Finding league history..."):
                    history_ids = SleeperService.get_league_history(selected_league['league_id'])
                    history_map = {}
                    for lid in history_ids:
                        l_data = SleeperService.get_league(lid)
                        if l_data:
                            history_map[l_data['season']] = lid
                    st.session_state.league_history_map = history_map

                # Season Filter
                available_seasons = sorted(list(history_map.keys()), reverse=True)
                selected_seasons = st.multiselect("Filter Seasons", options=available_seasons, default=available_seasons)

                if st.button("Analyze League History"):
                    # Map selected seasons back to IDs
                    selected_ids = [history_map[s] for s in selected_seasons]
                    load_data(selected_ids)
        else:
            st.warning("No leagues found for 2024. Try a different user?")

# Main Area
if st.session_state.analyzer:
    from views import trade_viewer
    from views import stats as stats_view

    # Reordered tabs and renamed
    tab1, tab2 = st.tabs(["League Summary", "Trade Log & Trees"])

    with tab1:
        stats_view.show(st.session_state.analyzer)

    with tab2:
        trade_viewer.show(st.session_state.analyzer)

else:
    st.info("Please enter your Sleeper username and select a league to begin.")
