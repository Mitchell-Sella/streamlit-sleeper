import streamlit as st
from sleeper_wrapper import User, League, Drafts
from utils import check_user, format_timestamp

st.title("Draft Assistant")
# st.session_state
    # user_name = Active username
    # user_id = Active user
    # user = API User object (do we need to store in the session state?)
    # league_id = Active league
    # league_ids = list of league ids for active user
    # league = API League object (do we need to store in the session state?)
    # draft_id = Active draft
    # draft_ids = list of all drafts for active user & active league
    # draft = API draft object (do we need to store in the session state?)


username = st.text_input(label="Enter Sleeper username:")
if username != "":
    user = User(username)
    leagues = user.get_all_leagues(sport="nfl", season=2024)
    # Create a dictionary of league names to league IDs
    league_dict = {league['name']: league['league_id'] for league in leagues}

    # Use the dictionary keys (league names) for the selectbox options
    league_id = st.selectbox("Select league:", options=list(league_dict.keys()))
    if league_id != "":
        # Get the league ID based on the selected league name
        league_id = league_dict[league_id]

        drafts = user.get_all_drafts(sport="nfl", season=2024)

        # Create a list of options for the dropdown
        options = [
            f"{format_timestamp(draft['start_time'])} - {draft['status']} (ID: {draft['draft_id']})"
            for draft in drafts if draft['league_id'] == league_id
        ]

        # Create the dropdown
        selected_option = st.selectbox("Select a draft:", options)

        # Extract the draft_id from the selected option
        if selected_option:
            selected_draft_id = selected_option.split("(ID: ")[-1].rstrip(")")

            # Find the selected draft in the original data
            selected_draft = next((draft for draft in drafts if draft['draft_id'] == selected_draft_id), None)
            if selected_draft:
                draft = Drafts(selected_draft_id)
                picks = draft.get_all_picks()
                user_picks = [
                    f"{pick['pick_no']} - {pick['metadata']['first_name']} {pick['metadata']['last_name']}"
                    for pick in picks if pick['picked_by'] == user.get_user_id()]
                st.write("Draft picks:")

                st.json(user_picks)


# draft_id = 1113489154534469633
# draft_id = 1128968894544347136
# draft = Drafts(draft_id)
# draft_picks = draft.get_all_picks()
# st.write(draft_picks)
# user_id = user.get_user_id()
#
# user_picks = [pick for pick in draft_picks if pick['picked_by'] == user_id]