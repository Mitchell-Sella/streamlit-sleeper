import requests
import streamlit as st

class SleeperService:
    BASE_URL = "https://api.sleeper.app/v1"
    @staticmethod
    @st.cache_data(ttl=3600)
    def get_traded_picks(league_id):
        """Fetch all traded picks in a league."""
        url = f"{SleeperService.BASE_URL}/league/{league_id}/traded_picks"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return []


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
    def get_all_transactions(league_ids, max_week=18):
        """
        Fetch all transactions for a list of league IDs.
        If league_ids is a string, treats it as a single ID.
        """
        if isinstance(league_ids, str):
            league_ids = [league_ids]

        all_transactions = []
        for lid in league_ids:
            # We iterate 1-18 for simplicity, though some seasons might be shorter/longer
            # or pre-season/off-season transactions might be in round 1 or other?
            # Sleeper transactions are usually round 1-18.
            # Offseason trades might be in round 1 of next season or round 18 of previous?
            # Actually sleeper puts transactions in 'round'.
            # Let's stick to 1-18 for now, maybe extending if needed.
            for week in range(1, max_week + 1):
                transactions = SleeperService.get_transactions(lid, week)
                if transactions:
                    all_transactions.extend(transactions)
        return all_transactions

    @staticmethod
    @st.cache_data(ttl=3600)
    def get_league_history(league_id):
        """
        Iteratively fetch previous league IDs to build a history.
        Returns a list of league IDs [current, prev, prev-prev, ...]
        """
        history = []
        current_id = league_id

        # Limit to avoid infinite loops if cycle exists (unlikely but safe)
        for _ in range(10):
            if not current_id:
                break

            history.append(current_id)

            league_data = SleeperService.get_league(current_id)
            if not league_data:
                break

            current_id = league_data.get('previous_league_id')

        return history

    @staticmethod
    @st.cache_data(ttl=86400) # Cache for 24 hours as players don't change often
    def get_all_players(sport="nfl"):
        """Fetch all players."""
        url = f"{SleeperService.BASE_URL}/players/{sport}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return {}

    @staticmethod
    @st.cache_data(ttl=3600)
    def get_drafts_in_league(league_id):
        """Fetch all drafts for a league."""
        url = f"{SleeperService.BASE_URL}/league/{league_id}/drafts"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return []

    @staticmethod
    @st.cache_data(ttl=3600)
    def get_draft(draft_id):
        """Fetch a specific draft."""
        url = f"{SleeperService.BASE_URL}/draft/{draft_id}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None

    @staticmethod
    @st.cache_data(ttl=3600)
    def get_draft_picks(draft_id):
        """Fetch all picks in a draft."""
        url = f"{SleeperService.BASE_URL}/draft/{draft_id}/picks"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return []
