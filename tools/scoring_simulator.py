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
    for week in range(1, 19):
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

def scoring_input(key, label, step=0.5, format="%.2f"):
    st.session_state.scoring[key] = st.number_input(
        label,
        value=st.session_state.scoring[key],
        step=step,
        format=format,
        key=key
    )

# Default scoring settings
default_scoring = {
    # Passing
    "pass_yd": 0.04, "pass_td": 4.0, "pass_int": -2.0, "pass_att": 0.0, "pass_cmp": 0.0, "pass_inc": 0.0, "pass_2pt": 2.0,
    # Rushing
    "rush_yd": 0.1, "rush_td": 6.0, "rush_att": 0.0, "rush_2pt": 2.0,
    # Receiving
    "rec": 1.0, "rec_yd": 0.1, "rec_td": 6.0, "rec_target": 0.0, "rec_2pt": 2.0,
    # Kicking
    "fgm": 3.0, "fgm_0_19": 3.0, "fgm_20_29": 3.0, "fgm_30_39": 3.0, "fgm_40_49": 4.0, "fgm_50p": 5.0,
    "fgmiss": -1.0, "xpm": 1.0, "xpmiss": -1.0,
    # Team Defense
    "def_td": 6.0, "pts_allow_0": 10.0, "pts_allow_1_6": 7.0, "pts_allow_7_13": 4.0, "pts_allow_14_20": 1.0,
    "pts_allow_21_27": 0.0, "pts_allow_28_34": -1.0, "pts_allow_35p": -4.0,
    # Special Teams Defense
    "blk_kick": 2.0, "def_st_td": 6.0, "def_st_ff": 1.0, "def_st_fum_rec": 1.0,
    # Special Teams Player
    "st_td": 6.0, "st_ff": 1.0, "st_fum_rec": 1.0,
    # Misc
    "fum_lost": -2.0, "fum_rec_td": 6.0,
    # Bonus
    "bonus_rush_yd_100": 3.0, "bonus_rush_yd_200": 6.0, "bonus_rec_yd_100": 3.0, "bonus_rec_yd_200": 6.0,
    "bonus_pass_yd_300": 3.0, "bonus_pass_yd_400": 6.0,
    # IDP
    "idp_solo": 1.0, "idp_asst": 0.5, "idp_sack": 2.0, "idp_int": 3.0, "idp_fum_force": 3.0, "idp_fum_rec": 2.0,
    "idp_def_td": 6.0, "idp_pass_def": 1.0, "idp_safety": 2.0, "idp_blk_kick": 2.0
}

# Function to randomize scoring settings
def randomize_scoring():
    return {k: round(random.uniform(-5, 10), 2) for k in default_scoring.keys()}

# Streamlit app
st.title("Season-Long Scoring Simulator")

# Season selection
season = st.selectbox("Select Season", options=[2023, 2022, 2021])

# Position multi-select
positions = st.multiselect("Select Positions", options=["QB", "RB", "WR", "TE", "K", "DEF", "IDP"], default=["QB", "RB", "WR", "TE"])

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

# Create tabs for different categories
tabs = st.tabs(["Passing", "Rushing", "Receiving", "Kicking", "Team Defense", "Special Teams", "Misc", "Bonus", "IDP"])

def scoring_input(key, label, step=0.5, format="%.2f"):
    st.session_state.scoring[key] = st.number_input(
        label,
        value=st.session_state.scoring[key],
        step=step,
        format=format,
        key=key
    )

# Passing Tab
with tabs[0]:
    st.subheader("Passing")
    scoring_input("pass_yd", "Points per Passing Yard", step=0.01)
    scoring_input("pass_td", "Points per Passing TD")
    scoring_input("pass_int", "Points per Interception")
    scoring_input("pass_att", "Points per Pass Attempt", step=0.1)
    scoring_input("pass_cmp", "Points per Pass Completion", step=0.1)
    scoring_input("pass_inc", "Points per Incomplete Pass", step=0.1)
    scoring_input("pass_2pt", "Points per 2PT Conversion")

# Rushing Tab
with tabs[1]:
    st.subheader("Rushing")
    scoring_input("rush_yd", "Points per Rushing Yard", step=0.01)
    scoring_input("rush_td", "Points per Rushing TD")
    scoring_input("rush_att", "Points per Rush Attempt", step=0.1)
    scoring_input("rush_2pt", "Points per 2PT Conversion (Rush)")

# Receiving Tab
with tabs[2]:
    st.subheader("Receiving")
    scoring_input("rec", "Points per Reception")
    scoring_input("rec_yd", "Points per Receiving Yard", step=0.01)
    scoring_input("rec_td", "Points per Receiving TD")
    scoring_input("rec_target", "Points per Target", step=0.1)
    scoring_input("rec_2pt", "Points per 2PT Conversion (Receiving)")

# Kicking Tab
with tabs[3]:
    st.subheader("Kicking")
    scoring_input("fgm", "Points per Field Goal Made")
    scoring_input("fgm_0_19", "Points per FG Made (0-19 yards)")
    scoring_input("fgm_20_29", "Points per FG Made (20-29 yards)")
    scoring_input("fgm_30_39", "Points per FG Made (30-39 yards)")
    scoring_input("fgm_40_49", "Points per FG Made (40-49 yards)")
    scoring_input("fgm_50p", "Points per FG Made (50+ yards)")
    scoring_input("fgmiss", "Points per Missed FG")
    scoring_input("xpm", "Points per Extra Point Made")
    scoring_input("xpmiss", "Points per Missed Extra Point")

# Team Defense Tab
with tabs[4]:
    st.subheader("Team Defense")
    scoring_input("def_td", "Points per Defensive TD")
    scoring_input("pts_allow_0", "Points for 0 Points Allowed")
    scoring_input("pts_allow_1_6", "Points for 1-6 Points Allowed")
    scoring_input("pts_allow_7_13", "Points for 7-13 Points Allowed")
    scoring_input("pts_allow_14_20", "Points for 14-20 Points Allowed")
    scoring_input("pts_allow_21_27", "Points for 21-27 Points Allowed")
    scoring_input("pts_allow_28_34", "Points for 28-34 Points Allowed")
    scoring_input("pts_allow_35p", "Points for 35+ Points Allowed")

# Special Teams Tab
with tabs[5]:
    st.subheader("Special Teams")
    scoring_input("blk_kick", "Points per Blocked Kick")
    scoring_input("def_st_td", "Points per Special Teams TD")
    scoring_input("def_st_ff", "Points per Special Teams Forced Fumble")
    scoring_input("def_st_fum_rec", "Points per Special Teams Fumble Recovery")
    scoring_input("st_td", "Points per Special Teams Player TD")
    scoring_input("st_ff", "Points per Special Teams Player Forced Fumble")
    scoring_input("st_fum_rec", "Points per Special Teams Player Fumble Recovery")

# Misc Tab
with tabs[6]:
    st.subheader("Misc")
    scoring_input("fum_lost", "Points per Fumble Lost")
    scoring_input("fum_rec_td", "Points per Fumble Recovery TD")

# Bonus Tab
with tabs[7]:
    st.subheader("Bonus")
    scoring_input("bonus_rush_yd_100", "Bonus Points for 100-199 Rushing Yards")
    scoring_input("bonus_rush_yd_200", "Bonus Points for 200+ Rushing Yards")
    scoring_input("bonus_rec_yd_100", "Bonus Points for 100-199 Receiving Yards")
    scoring_input("bonus_rec_yd_200", "Bonus Points for 200+ Receiving Yards")
    scoring_input("bonus_pass_yd_300", "Bonus Points for 300-399 Passing Yards")
    scoring_input("bonus_pass_yd_400", "Bonus Points for 400+ Passing Yards")

# IDP Tab
with tabs[8]:
    st.subheader("IDP (Individual Defensive Players)")
    scoring_input("idp_solo", "Points per Solo Tackle")
    scoring_input("idp_asst", "Points per Assisted Tackle")
    scoring_input("idp_sack", "Points per Sack")
    scoring_input("idp_int", "Points per Interception")
    scoring_input("idp_fum_force", "Points per Forced Fumble")
    scoring_input("idp_fum_rec", "Points per Fumble Recovery")
    scoring_input("idp_def_td", "Points per Defensive TD")
    scoring_input("idp_pass_def", "Points per Pass Defended")
    scoring_input("idp_safety", "Points per Safety")
    scoring_input("idp_blk_kick", "Points per Blocked Kick")
    
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

            # Optional: Add a download button for the full results
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download Full Results",
                data=csv,
                file_name=f"fantasy_scores_{season}.csv",
                mime="text/csv",
            )

        else:
            st.error("Failed to retrieve player stats. Please try again.")