import streamlit as st
import pandas as pd
import json


def init_session_state():
    """
    Initialize the session state.
    """
    if "perm" not in st.session_state:
        st.session_state.perm = {
            "user_name": "",
            "league_name": "",
            "draft_id": "",
            "rankings": pd.DataFrame(columns=['player_id', 'full_name', 'position', 'team_abbr', 'rank', 'tier', 'salary_cap']),
        }
    if "temp_username" not in st.session_state:
        st.session_state.temp_username = ""

def create_header():
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Field 1")
        with col2:
            st.text_input("Field 2")


@st.cache_data
def load_players(file_path, keys):
    """
    Load and filter player data from a JSON file.
    :param file_path: Path to the JSON file.
    :type file_path: str
    :param keys: List of fields to keep in the output.
    :type keys: list
    :return: Player data.
    :rtype: pd.DataFrame
    """
    # Load the JSON file
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Filter the data to include only the selected fields
    players_json = [{key: player[key] for key in keys if key in player} for player in data.values()]

    # Convert to a pandas DataFrame
    players = pd.DataFrame(players_json)

    return players