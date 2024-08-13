import streamlit as st
from sleeper_wrapper import User

def run():
    """
    Main function for Hello World.
    """
    # Set page config
    st.set_page_config(
        page_title="Home",
        page_icon="https://sleeper.com/favicon.ico",
    )

    st.image("https://sleepercdn.com/images/v2/logos/logo_with_text_2.png")

    st.text_input(label="Enter Sleeper Username:", key="username")
    if st.session_state.username != "":
        user = User(st.session_state.username)
        leagues = user.get_all_leagues(sport="nfl", season=2024)
        st.session_state.leagues = [league['name'] for league in leagues]
        st.session_state.league_ids = [league['league_id'] for league in leagues]
        st.session_state.league_id_map = {league['name']: league['league_id'] for league in leagues}
        st.selectbox(label="Select League", options=st.session_state.leagues, key="league")
        st.session_state.league_id = st.session_state.league_id_map[st.session_state.league]
        st.write(st.session_state.league_id)


if __name__ == "__main__":
    run()
