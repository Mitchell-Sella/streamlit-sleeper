import streamlit as st
from sleeper_wrapper import User
from utils import init_session_state

# Set page config
st.set_page_config(
    page_title="Sleeper",
    page_icon="https://sleeper.com/favicon.ico",
)

# Initialize session state
init_session_state()


def check_username_exists(username):
    """
    Check if username exists in Sleeper API.
    :param username: username to check
    :type username: str
    :return: True if username exists in Sleeper API, else False
    :rtype: bool
    """
    try:
        user = User(username)
        user_data = user.get_user()
        return user_data is not None and user_data != {}
    except:
        return False


def update_username():
    """
    Update username in session state if username exists in Sleeper API.
    """
    new_username = st.session_state.temp_username
    if check_username_exists(new_username):
        st.session_state.persistent_data['user_name'] = new_username
        st.session_state.username_valid = True
    else:
        st.session_state.username_valid = False


def select_league():
    """
    Create select box object for user to select league.
    """
    if st.session_state.persistent_data['user_name']:
        user = User(st.session_state.persistent_data['user_name'])
        leagues = user.get_all_leagues(sport="nfl", season=2024)
        league_dict = {league['name']: league['league_id'] for league in leagues}
        league_name = st.selectbox("Select league", options=[""] + list(league_dict.keys()))
        if league_name != "":
            st.session_state.persistent_data['league_name'] = league_name
            st.session_state.persistent_data['league_id'] = league_dict[league_name]


# Sidebar for user input and league selection
with st.sidebar:
    st.text_input(
        label="Enter Sleeper username",
        key="temp_username",
        value=st.session_state.persistent_data['user_name'],
        on_change=update_username
    )

    if 'username_valid' in st.session_state:
        if st.session_state.username_valid:
            select_league()
        else:
            st.error(f"'{st.session_state.temp_username}' is not a Sleeper username.")

# Create draft assistant page object
draft_assistant = st.Page(
    "draft/draft_assistant.py", title="Draft Assistant", icon=":material/psychology_alt:", default=True
)

# Create draft reviewer page object
draft_reviewer = st.Page(
    "draft/draft_reviewer.py", title="Draft Reviewer", icon=":material/dashboard:"
)

# Create guillotine page object
guillotine = st.Page(
    "in-season/guillotine.py", title="Guillotine", icon=":material/content_cut:"
)

# Create page navigation structure
pg = st.navigation(
    {
        "Draft": [draft_assistant, draft_reviewer],
        "In-Season": [guillotine],
    }
)

# Run page
pg.run()