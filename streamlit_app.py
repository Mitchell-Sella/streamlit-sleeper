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
    """Fetch data for selected league and initialize analyzer."""
    if st.session_state.selected_league:
        league_id = st.session_state.selected_league['league_id']

        with st.spinner("Fetching league data..."):
            rosters = SleeperService.get_rosters(league_id)
            users = SleeperService.get_users_in_league(league_id)
            # Transactions for current season (1-18)
            transactions = SleeperService.get_all_transactions(league_id)

            # Initialize Analyzer
            st.session_state.analyzer = LeagueAnalyzer(transactions, rosters, users)
            st.success("Data loaded!")

# Sidebar
with st.sidebar:
    st.title("Sleeper Network")

    username = st.text_input("Sleeper Username")
    season = st.selectbox("Season", options=["2024", "2023", "2022", "2021", "2020"], index=0)

    if st.button("Load User"):
        if username:
            user = SleeperService.get_user(username)
            if user:
                st.session_state.user = user
                # Fetch leagues
                leagues = SleeperService.get_all_leagues(user['user_id'], season=season)
                st.session_state.leagues = leagues
            else:
                st.error("User not found.")
        else:
            st.warning("Please enter a username.")

    if st.session_state.user:
        st.write(f"Logged in as: **{st.session_state.user['display_name']}**")

        league_options = {l['name']: l for l in st.session_state.leagues}
        selected_league_name = st.selectbox("Select League", options=list(league_options.keys()))

        if selected_league_name:
            st.session_state.selected_league = league_options[selected_league_name]

        if st.button("Analyze League"):
            load_data()

# Main Area
if st.session_state.analyzer:
    import views.trade_network as trade_network
    import views.player_explorer as player_explorer
    import views.stats as stats_view

    tab1, tab2, tab3 = st.tabs(["Trade Network", "Player Explorer", "League Stats"])

    with tab1:
        trade_network.show(st.session_state.analyzer)

    with tab2:
        player_explorer.show(st.session_state.analyzer)

    with tab3:
        stats_view.show(st.session_state.analyzer)

else:
    st.info("Please enter your Sleeper username and select a league to begin.")
