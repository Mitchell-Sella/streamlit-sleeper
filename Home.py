import streamlit as st
from sleeper_wrapper import User

def run():
    """
    Main function for home page.
    """
    # Set page config
    st.set_page_config(
        page_title="Home",
        page_icon="https://sleeper.com/favicon.ico",
    )

    # st.image("https://sleepercdn.com/images/v2/logos/logo_with_text_2.png")
    #
    # st.text_input(label="Enter Sleeper username", key="username")
    # if st.session_state.username != "":
    #     st.session_state.user = User(st.session_state.username)
    #     leagues = st.session_state.user.get_all_leagues(sport="nfl", season=2024)
    #     # Create a dictionary of league names to league IDs
    #     league_dict = {league['name']: league['league_id'] for league in leagues}
    #
    #     # Use the dictionary keys (league names) for the selectbox options
    #     st.selectbox("Select league", options=list(league_dict.keys()), key="selected_league")
    #
    #     # Get the league ID based on the selected league name
    #     st.session_state.league_id = league_dict[st.session_state.selected_league]


if __name__ == "__main__":
    run()
