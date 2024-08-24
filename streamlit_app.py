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
        st.session_state.perm['user_name'] = new_username
        st.session_state.username_valid = True
    else:
        st.session_state.username_valid = False


def select_league():
    """
    Create select box object for user to select league.
    """
    if st.session_state.perm['user_name']:
        user = User(st.session_state.perm['user_name'])
        leagues = user.get_all_leagues(sport="nfl", season=2024)
        league_dict = {league['name']: league['league_id'] for league in leagues}
        league_name = st.selectbox(":football: Select League", options=[""] + list(league_dict.keys()))
        if league_name != "":
            st.session_state.perm['league_name'] = league_name
            st.session_state.perm['league_id'] = league_dict[league_name]


# Sidebar for user input and league selection
with st.sidebar:
    st.text_input(
        label=":bust_in_silhouette: Enter Username",
        key="temp_username",
        value=st.session_state.perm['user_name'],
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

# Create guillotine page object
guillotine_dashboard = st.Page(
    "in-season/guillotine_dashboard.py", title="Guillotine Dashboard", icon=":material/content_cut:"
)

# Create bizzaro page object
bizzaro_dashboard = st.Page(
    "in-season/bizzaro_dashboard.py", title="Bizzaro Dashboard", icon=":material/delete:"
)

# Rankings builder
rankings_builder = st.Page(
    "tools/rankings_builder.py", title="Rankings Builder", icon=":material/format_list_numbered:"
)

# Scoring simulator
scoring_simulator = st.Page(
    "tools/scoring_simulator.py", title="Scoring Simulator", icon=":material/tune:"
)

# Create page navigation structure
pg = st.navigation(
    {
        "Draft": [draft_assistant],
        "In-Season": [guillotine_dashboard, bizzaro_dashboard],
        "Tools": [rankings_builder, scoring_simulator],
    }
)

# Run page
pg.run()