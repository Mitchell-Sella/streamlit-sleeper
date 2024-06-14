import streamlit as st
import requests


def get_users_in_league(league_id):
    base_url = 'https://api.sleeper.app'
    endpoint = f'/v1/league/{league_id}/users'
    response = requests.get(base_url + endpoint)
    if response.status_code == 200:
        return response.json()
    else:
        return None


def get_trades_for_user(league_id, user_id):
    base_url = 'https://api.sleeper.app'
    endpoint = f'/v1/league/{league_id}/trades'
    response = requests.get(base_url + endpoint)
    if response.status_code == 200:
        trades = response.json()
        user_trades = [trade for trade in trades if user_id in [trade['user_id'], trade['partner_id']]]
        return user_trades
    else:
        return None
    

def get_players():
    url = "https://api.sleeper.app/v1/players/nfl"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None


def main():
    st.set_page_config(
        page_title="Trade Tracker",
        page_icon="https://sleeper.com/favicon.ico",
    )

    st.title('Sleeper League Users and Trades Viewer')

    league_id = st.text_input('Enter League ID:')
    if st.button('Get Users'):
        if league_id:
            users = get_users_in_league(league_id)
            if users:
                st.write(f'Users in League {league_id}:')
                user_ids = {user['user_id']: user['display_name'] for user in users}
                selected_user_id = st.selectbox('Select a User:', list(user_ids.values()))

                if st.button('View Trades'):
                    trades = get_trades_for_user(league_id, list(user_ids.keys())[list(user_ids.values()).index(selected_user_id)])
                    if trades:
                        st.write(f"Trades for {selected_user_id}:")
                        for trade in trades:
                            st.write(trade)
                    else:
                        st.write(f"No trades found for {selected_user_id}")
            else:
                st.write(f"Failed to fetch users for League ID: {league_id}")
        else:
            st.write('Please enter a League ID')

if __name__ == "__main__":
    main()
