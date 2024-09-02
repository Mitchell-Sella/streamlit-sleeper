import streamlit as st
import pandas as pd
from sleeper_wrapper import Drafts, User
import colorsys

# Initialize session state
if 'username' not in st.session_state:
    st.session_state.username = ''
if 'budgets' not in st.session_state:
    st.session_state.budgets = {}
if 'tier_values' not in st.session_state:
    st.session_state.tier_values = {}
if 'merged_df' not in st.session_state:
    st.session_state.merged_df = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'rankings_df' not in st.session_state:
    st.session_state.rankings_df = None


# Function to load rankings
def load_rankings(uploaded_file):
    df = pd.read_csv(uploaded_file)

    # Ensure required columns exist
    required_columns = ['player_id', 'Name', 'Position', 'Tier']
    if not all(col in df.columns for col in required_columns):
        st.error("The uploaded file is missing one or more required columns: player_id, Name, Position, Tier")
        return None

    df['player_id'] = df['player_id'].astype(str)
    return df


# Function to color-code rows by tier
def color_code_tiers(val):
    color_map = {
        1: '#FF4136', 2: '#FF851B', 3: '#FFDC00', 4: '#2ECC40',
        5: '#0074D9', 6: '#B10DC9', 7: '#FF6F61', 8: '#7FDBFF'
    }
    return f'background-color: {color_map.get(val, "#FFFFFF")}; color: black;'


# Function to color-code remaining budget
def color_remaining(val):
    if pd.isna(val):
        return ''
    if val > 0:
        return 'background-color: #2ECC40; color: black;'
    elif val < 0:
        return 'background-color: #FF4136; color: black;'
    else:
        return 'background-color: #FFDC00; color: black;'


# Function to color-code value difference
def color_value_difference(val):
    if pd.isna(val):
        return ''

    max_intensity, min_intensity = 0.7, 0.2

    if val > 0:
        hue = 0.33  # Green hue
        intensity = min(val / 5, 1) * (max_intensity - min_intensity) + min_intensity
        r, g, b = colorsys.hsv_to_rgb(hue, 0.7, intensity)
    elif val < 0:
        hue = 0.0  # Red hue
        intensity = min(abs(val) / 5, 1) * (max_intensity - min_intensity) + min_intensity
        r, g, b = colorsys.hsv_to_rgb(hue, 0.7, intensity)
    else:
        r, g, b = 1, 1, 1

    bg_color = f'#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}'
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    text_color = 'black' if brightness > 0.5 else 'white'

    return f'background-color: {bg_color}; color: {text_color};'


# Function to fetch and process draft data
def fetch_and_process_draft_data(draft_id, username):
    try:
        draft = Drafts(draft_id)
        picks = draft.get_all_picks()

        processed_picks = []
        for pick in picks:
            processed_picks.append({
                'player_id': str(pick['player_id']),
                'amount': float(pick['metadata'].get('amount', 0)),
                'picked_by': pick['picked_by'],
            })

        draft_df = pd.DataFrame(processed_picks)

        merged_df = pd.merge(st.session_state.rankings_df, draft_df, on='player_id', how='left')

        user = User(username)
        user_id = user.get_user_id()

        return merged_df, user_id
    except Exception as e:
        st.error(f"Failed to fetch or process draft data: {str(e)}")
        return None, None


st.title("Fantasy Football Draft Analyzer")

# File uploader for rankings
uploaded_file = st.file_uploader("Upload rankings CSV file", type="csv")
if uploaded_file is not None:
    st.session_state.rankings_df = load_rankings(uploaded_file)
    if st.session_state.rankings_df is not None:
        st.success("Rankings file uploaded successfully!")

        # Dynamically create budget inputs based on unique positions
        positions = st.session_state.rankings_df['Position'].unique()
        st.session_state.budgets = {pos: st.session_state.budgets.get(pos, 0) for pos in positions}

        # Dynamically create tier value inputs based on unique tiers
        tiers = st.session_state.rankings_df['Tier'].unique()
        st.session_state.tier_values = {tier: st.session_state.tier_values.get(tier, 0) for tier in tiers}

# Draft ID and Username Input (Collapsible)
with st.expander("Enter League and User Information", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        draft_id = st.text_input("Enter Sleeper Draft ID:", key="draft_id")
    with col2:
        username = st.text_input("Enter Sleeper Username:", key="username")

# Budget Input Section (Collapsible)
if st.session_state.rankings_df is not None:
    with st.expander("Set Position Budgets", expanded=False):
        cols = st.columns(4)
        for i, (pos, budget) in enumerate(st.session_state.budgets.items()):
            with cols[i % 4]:
                st.session_state.budgets[pos] = st.number_input(f"{pos} Budget", value=budget, min_value=0, step=1)

# Tier Value Input Section (Collapsible)
if st.session_state.rankings_df is not None:
    with st.expander("Set Projected Tier Values", expanded=False):
        cols = st.columns(4)
        for i, (tier, value) in enumerate(st.session_state.tier_values.items()):
            with cols[i % 4]:
                st.session_state.tier_values[tier] = st.number_input(f"Tier {tier} Value", value=value, min_value=0,
                                                                     step=1)

# Refresh button
if st.button("Refresh Draft Data"):
    if draft_id and username and st.session_state.rankings_df is not None:
        st.session_state.merged_df, st.session_state.user_id = fetch_and_process_draft_data(draft_id, username)
        if st.session_state.merged_df is not None:
            st.success("Draft data fetched and processed successfully!")
        else:
            st.warning("No valid draft data to analyze.")
    else:
        st.warning("Please upload rankings file and enter both Draft ID and Username before refreshing.")

# If we have draft data, display the analysis
if st.session_state.merged_df is not None:
    merged_df = st.session_state.merged_df
    user_id = st.session_state.user_id

    # Filter for user's roster
    user_roster = merged_df[merged_df['picked_by'] == user_id]

    # Create two columns for budget and tier spending
    col1, col2 = st.columns(2)

    with col1:
        # Budget and Spent by Position
        st.subheader("Budget and Spent by Position")
        position_budget = st.session_state.budgets

        spent_by_position = user_roster.groupby('Position')['amount'].sum()
        budget_vs_spent = pd.DataFrame({
            'Budget': position_budget,
            'Spent': spent_by_position,
            'Remaining': pd.Series(position_budget) - spent_by_position
        }).fillna(0)

        styled_budget = budget_vs_spent.style.applymap(color_remaining, subset=['Remaining'])
        st.write(styled_budget.format("${:.2f}"))

        # Total Spent
        total_spent = user_roster['amount'].sum()
        st.write(f"Total Spent: ${total_spent:.2f}")

    with col2:
        # Average Amount Spent by Tier
        st.subheader("Average Amount Spent by Tier")
        tier_spending = merged_df[merged_df['picked_by'].notnull()].groupby('Tier')['amount'].mean().sort_index()
        tier_spending = tier_spending[tier_spending.index <= 8]  # Only top 8 tiers

        tier_spending_df = pd.DataFrame({
            'Tier': tier_spending.index,
            'Avg Spent': tier_spending.values
        })

        st.write(tier_spending_df.style.format({'Avg Spent': '${:.2f}'}))

    # Display merged dataframe with filters
    st.subheader("Merged Rankings and Draft Data")

    # Add filter selections
    col1, col2, col3 = st.columns(3)
    with col1:
        draft_filter = st.selectbox(
            "Filter by draft status:",
            ("All Players", "Drafted Players", "Undrafted Players")
        )
    with col2:
        position_filter = st.multiselect(
            "Filter by position:",
            options=sorted(merged_df['Position'].unique().tolist()),
            default=sorted(merged_df['Position'].unique().tolist())
        )
    with col3:
        tier_filter = st.multiselect(
            "Filter by tier:",
            options=sorted(merged_df['Tier'].unique().tolist()),
            default=sorted(merged_df['Tier'].unique().tolist())
        )

    # Apply filters
    if draft_filter == "Drafted Players":
        filtered_df = merged_df[merged_df['picked_by'].notnull()]
    elif draft_filter == "Undrafted Players":
        filtered_df = merged_df[merged_df['picked_by'].isnull()]
    else:
        filtered_df = merged_df

    if position_filter:
        filtered_df = filtered_df[filtered_df['Position'].isin(position_filter)]

    if tier_filter:
        filtered_df = filtered_df[filtered_df['Tier'].isin(tier_filter)]

    # Add projected tier value and calculate difference
    filtered_df['Projected Value'] = filtered_df['Tier'].map(st.session_state.tier_values)
    filtered_df['Value Difference'] = filtered_df['Projected Value'] - filtered_df['amount']

    # Rename columns for display
    filtered_df = filtered_df.rename(columns={
        'picked_by': 'Picked By',
        'amount': 'Amount Spent'
    })

    # Reorder columns
    base_columns = ['Name', 'Position', 'Team', 'Tier']
    extra_columns = [col for col in filtered_df.columns if
                     col not in base_columns + ['Projected Value', 'Amount Spent', 'Value Difference', 'Picked By',
                                                'player_id']]
    value_columns = ['Projected Value', 'Amount Spent', 'Value Difference', 'Picked By']

    column_order = base_columns + extra_columns + value_columns
    filtered_df = filtered_df[column_order]

    # Display filtered dataframe with color-coded tiers and value difference
    st.dataframe(filtered_df.style
                 .applymap(color_code_tiers, subset=['Tier'])
                 .applymap(color_value_difference, subset=['Value Difference'])
                 .format({'Amount Spent': '${:.2f}', 'Projected Value': '${:.2f}', 'Value Difference': '${:.2f}'}))