import streamlit as st
import pandas as pd
import random
from sleeper_wrapper import Players, Stats

# Initialize Sleeper API wrappers
players = Players()
stats = Stats()

# Function to get player stats for the entire season
def get_season_stats(season):
    season_stats = {}
    for week in range(1, 19):  # NFL regular season has 18 weeks
        week_stats = stats.get_week_stats("regular", season, week)
        for player_id, stat_line in week_stats.items():
            if player_id not in season_stats:
                season_stats[player_id] = stat_line
            else:
                for stat, value in stat_line.items():
                    season_stats[player_id][stat] = season_stats[player_id].get(stat, 0) + value
    return season_stats

# Function to calculate player scores based on custom settings
def calculate_scores(player_stats, scoring_settings):
    scores = {}
    for player_id, stat_line in player_stats.items():
        score = sum(stat_line.get(stat, 0) * value for stat, value in scoring_settings.items())
        scores[player_id] = score
    return scores

# Default scoring settings
default_scoring = {
    "pass_yd": 0.04, "pass_td": 4.0, "pass_int": -2.0, "pass_att": 0.0, "pass_cmp": 0.0,
    "rush_yd": 0.1, "rush_td": 6.0, "rush_att": 0.0,
    "rec": 1.0, "rec_yd": 0.1, "rec_td": 6.0, "rec_target": 0.0,
    "fum_lost": -2.0, "sack": 1.0, "safe": 2.0, "def_td": 6.0, "blk_kick": 2.0, "ret_td": 6.0
}

# Function to randomize scoring settings
def randomize_scoring():
    return {k: round(random.uniform(-5, 10), 2) for k in default_scoring.keys()}

# Streamlit app
st.title("Season-Long Scoring Simulator")

# Season selection
season = st.selectbox("Select Season", options=[2023, 2022, 2021])

# Position multi-select
positions = st.multiselect("Select Positions", options=["QB", "RB", "WR", "TE", "K", "DEF"], default=["QB", "RB", "WR", "TE"])

# Randomize and Reset buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("Randomize Scoring"):
        st.session_state.scoring = randomize_scoring()
with col2:
    if st.button("Reset to Default"):
        st.session_state.scoring = default_scoring.copy()

# Initialize session state for scoring if not exists
if 'scoring' not in st.session_state:
    st.session_state.scoring = default_scoring.copy()

# User inputs for scoring settings
st.header("Scoring Settings")

# Create three columns for passing, rushing, and receiving
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Passing")
    st.session_state.scoring["pass_yd"] = st.number_input("Points per Passing Yard", value=st.session_state.scoring["pass_yd"], step=0.01, format="%.2f")
    st.session_state.scoring["pass_td"] = st.number_input("Points per Passing TD", value=st.session_state.scoring["pass_td"], step=0.5)
    st.session_state.scoring["pass_int"] = st.number_input("Points per Interception", value=st.session_state.scoring["pass_int"], step=0.5)
    st.session_state.scoring["pass_att"] = st.number_input("Points per Pass Attempt", value=st.session_state.scoring["pass_att"], step=0.1)
    st.session_state.scoring["pass_cmp"] = st.number_input("Points per Pass Completion", value=st.session_state.scoring["pass_cmp"], step=0.1)

with col2:
    st.subheader("Rushing")
    st.session_state.scoring["rush_yd"] = st.number_input("Points per Rushing Yard", value=st.session_state.scoring["rush_yd"], step=0.01, format="%.2f")
    st.session_state.scoring["rush_td"] = st.number_input("Points per Rushing TD", value=st.session_state.scoring["rush_td"], step=0.5)
    st.session_state.scoring["rush_att"] = st.number_input("Points per Rush Attempt", value=st.session_state.scoring["rush_att"], step=0.1)

with col3:
    st.subheader("Receiving")
    st.session_state.scoring["rec"] = st.number_input("Points per Reception", value=st.session_state.scoring["rec"], step=0.5)
    st.session_state.scoring["rec_yd"] = st.number_input("Points per Receiving Yard", value=st.session_state.scoring["rec_yd"], step=0.01, format="%.2f")
    st.session_state.scoring["rec_td"] = st.number_input("Points per Receiving TD", value=st.session_state.scoring["rec_td"], step=0.5)
    st.session_state.scoring["rec_target"] = st.number_input("Points per Target", value=st.session_state.scoring["rec_target"], step=0.1)

# Additional categories
st.subheader("Additional Categories")
col4, col5 = st.columns(2)

with col4:
    st.session_state.scoring["fum_lost"] = st.number_input("Points per Fumble Lost", value=st.session_state.scoring["fum_lost"], step=0.5)
    st.session_state.scoring["sack"] = st.number_input("Points per Sack (for DST)", value=st.session_state.scoring["sack"], step=0.5)
    st.session_state.scoring["safe"] = st.number_input("Points per Safety (for DST)", value=st.session_state.scoring["safe"], step=0.5)

with col5:
    st.session_state.scoring["def_td"] = st.number_input("Points per Pick Six (for DST)", value=st.session_state.scoring["def_td"], step=0.5)
    st.session_state.scoring["blk_kick"] = st.number_input("Points per Blocked Kick (for DST)", value=st.session_state.scoring["blk_kick"], step=0.5)
    st.session_state.scoring["ret_td"] = st.number_input("Points per Return TD (for DST)", value=st.session_state.scoring["ret_td"], step=0.5)

if st.button("Calculate Season Scores"):
    with st.spinner("Fetching and calculating season stats..."):
        # Get player stats for the entire season
        player_stats = get_season_stats(season)

        if player_stats:
            # Calculate scores based on custom settings
            scores = calculate_scores(player_stats, st.session_state.scoring)

            # Get player details
            all_players = players.get_all_players()

            # Create a dataframe with player details and scores
            data = []
            for player_id, score in scores.items():
                if player_id in all_players:
                    player = all_players[player_id]
                    if player['position'] in positions:
                        data.append({
                            "Player": f"{player['first_name']} {player['last_name']}",
                            "Position": player['position'],
                            "Team": player['team'],
                            "Total Score": round(score, 2)
                        })

            df = pd.DataFrame(data)
            df = df.sort_values("Total Score", ascending=False).reset_index(drop=True)

            # Display top players
            st.header(f"Top Players for {season} Season")
            st.dataframe(df.head(50))

        else:
            st.error("Failed to retrieve player stats. Please try again.")