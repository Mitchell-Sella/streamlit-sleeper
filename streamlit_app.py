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

def load_data():
    """Fetch data for selected league (and history) and initialize analyzer."""
    if st.session_state.selected_league:
        league_id = st.session_state.selected_league['league_id']

        with st.spinner("Fetching league history and data..."):
            # 1. Fetch history
            history_ids = SleeperService.get_league_history(league_id)

            # 2. Fetch rosters & users (from current league mostly, but history matters for names?)
            # Actually, names change. But we usually map to current owners or user IDs.
            # For simplicity, use current league's roster/user map.
            rosters = SleeperService.get_rosters(league_id)
            users = SleeperService.get_users_in_league(league_id)

            # 3. Fetch transactions for ALL leagues in history
            transactions = SleeperService.get_all_transactions(history_ids)

            # 4. Fetch players
            all_players = SleeperService.get_all_players()

            # Initialize Analyzer
            st.session_state.analyzer = LeagueAnalyzer(transactions, rosters, users, all_players)
            st.success(f"Loaded {len(history_ids)} seasons of data with {len(transactions)} transactions!")

# Sidebar
with st.sidebar:
    st.title("Sleeper Network")

    username = st.text_input("Sleeper Username")
    # Removed Season selector as requested

    if st.button("Load User"):
        if username:
            user = SleeperService.get_user(username)
            if user:
                st.session_state.user = user
                # Fetch leagues - try recent years if 2024 fails
                found_leagues = []
                for year in ["2024", "2023", "2022"]:
                    leagues = SleeperService.get_all_leagues(user['user_id'], season=year)
                    if leagues:
                        found_leagues = leagues
                        break

                st.session_state.leagues = found_leagues
                if not found_leagues:
                    st.warning("No recent leagues found (2022-2024).")
            else:
                st.error("User not found.")
        else:
            st.warning("Please enter a username.")

    if st.session_state.user:
        st.write(f"Logged in as: **{st.session_state.user['display_name']}**")

        league_options = {l['name']: l for l in st.session_state.leagues}
        if league_options:
            selected_league_name = st.selectbox("Select League", options=list(league_options.keys()))

            if selected_league_name:
                st.session_state.selected_league = league_options[selected_league_name]

            if st.button("Analyze League History"):
                load_data()
        else:
            st.warning("No leagues found for 2024. Try a different user?")

# Main Area
if st.session_state.analyzer:
    from views import trade_network
    from views import trade_viewer
    from views import stats as stats_view

    tab1, tab2, tab3 = st.tabs(["Trade Network", "Trade Log & Trees", "League Stats"])

    with tab1:
        trade_network.show(st.session_state.analyzer)

    with tab2:
        trade_viewer.show(st.session_state.analyzer)

    with tab3:
        stats_view.show(st.session_state.analyzer)

else:
    st.info("Please enter your Sleeper username and select a league to begin.")
