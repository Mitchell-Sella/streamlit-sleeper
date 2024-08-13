import streamlit as st
from sleeper_wrapper import User, League, Draft

st.title("🏈 Sleeper Draft Analyzer")

# User input
username = st.text_input("Enter Sleeper username:")

if username:
    user = User(username)
    user_id = user.get_user_id()

    if user_id:
        st.success(f"User found: {username}")

        # Get user's leagues
        leagues = user.get_all_leagues("nfl", 2023)  # Adjust year as needed
        league_names = [league['name'] for league in leagues]
        selected_league = st.selectbox("Select a league:", league_names)

        if selected_league:
            league_id = next(league['league_id'] for league in leagues if league['name'] == selected_league)
            league = League(league_id)
            draft_id = league.get_draft_id()

            if draft_id:
                draft = Draft(draft_id)
                draft_picks = draft.get_all_picks()

                st.subheader("Draft Analysis")

                # Analyze draft picks
                user_picks = [pick for pick in draft_picks if pick['picked_by'] == user_id]

                st.write(f"Total picks by {username}: {len(user_picks)}")

                # Display user's picks
                st.write("Your draft picks:")
                for pick in user_picks:
                    st.write(
                        f"Round {pick['round']}, Pick {pick['pick_no']}: {pick['metadata']['first_name']} {pick['metadata']['last_name']} ({pick['metadata']['position']})")

                # Additional analysis can be added here
                # For example, positional breakdown, average draft position, etc.

                # Positional breakdown
                positions = [pick['metadata']['position'] for pick in user_picks]
                position_counts = {pos: positions.count(pos) for pos in set(positions)}

                st.subheader("Positional Breakdown")
                for pos, count in position_counts.items():
                    st.write(f"{pos}: {count}")

            else:
                st.error("No draft found for this league.")
    else:
        st.error("User not found. Please check the username and try again.")