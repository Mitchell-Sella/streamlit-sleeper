import requests
import streamlit as st

class SleeperService:
    BASE_URL = "https://api.sleeper.app/v1"

    @staticmethod
    @st.cache_data(ttl=3600)
    def get_user(username):
        """Fetch user details by username."""
        url = f"{SleeperService.BASE_URL}/user/{username}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None

    @staticmethod
    @st.cache_data(ttl=3600)
    def get_all_leagues(user_id, sport="nfl", season="2024"):
        """Fetch all leagues for a user for a given sport and season."""
        url = f"{SleeperService.BASE_URL}/user/{user_id}/leagues/{sport}/{season}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return []

    @staticmethod
    @st.cache_data(ttl=3600)
    def get_league(league_id):
        """Fetch details for a specific league."""
        url = f"{SleeperService.BASE_URL}/league/{league_id}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None

    @staticmethod
    @st.cache_data(ttl=3600)
    def get_rosters(league_id):
        """Fetch rosters for a league."""
        url = f"{SleeperService.BASE_URL}/league/{league_id}/rosters"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return []

    @staticmethod
    @st.cache_data(ttl=3600)
    def get_users_in_league(league_id):
        """Fetch users in a league."""
        url = f"{SleeperService.BASE_URL}/league/{league_id}/users"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return []

    @staticmethod
    @st.cache_data(ttl=3600)
    def get_transactions(league_id, round):
        """Fetch transactions for a specific round (week)."""
        url = f"{SleeperService.BASE_URL}/league/{league_id}/transactions/{round}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return []

    @staticmethod
    @st.cache_data(ttl=3600)
    def get_all_transactions(league_id, max_week=18):
        """Fetch all transactions for the season (weeks 1 to max_week)."""
        all_transactions = []
        for week in range(1, max_week + 1):
            transactions = SleeperService.get_transactions(league_id, week)
            if transactions:
                all_transactions.extend(transactions)
        return all_transactions

    @staticmethod
    @st.cache_data(ttl=86400) # Cache for 24 hours as players don't change often
    def get_all_players(sport="nfl"):
        """Fetch all players."""
        url = f"{SleeperService.BASE_URL}/players/{sport}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return {}
