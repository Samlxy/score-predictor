import os
import random
import logging
import requests
from datetime import datetime, timedelta
from dateutil import parser
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
API_KEY = os.getenv('API_FOOTBALL_KEY')
API_HOST = os.getenv('API_FOOTBALL_HOST', 'api-football-v1.p.rapidapi.com')
BASE_URL = 'https://api-football-v1.p.rapidapi.com/v3/'

# Headers for API requests
HEADERS = {
    'x-rapidapi-key': API_KEY,
    'x-rapidapi-host': API_HOST
}

def make_api_request(endpoint, params=None):
    """Helper function to make API requests with error handling"""
    if not API_KEY:
        logger.error("API key not found. Please set API_FOOTBALL_KEY in your .env file")
        return None
        
    try:
        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=HEADERS,
            params=params or {}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def fetch_matches(start_date, end_date):
    """
    Fetch football matches from API-Football within the specified date range.
    
    Args:
        start_date (datetime): Start date for matches
        end_date (datetime): End date for matches
        
    Returns:
        list: List of match dictionaries with team, league, and odds information
    """
    if not API_KEY:
        logger.error("API key not configured. Using sample data instead.")
        return get_sample_matches(start_date, end_date)
    
    try:
        # Convert dates to strings in YYYY-MM-DD format
        from_date = start_date.strftime('%Y-%m-%d')
        to_date = end_date.strftime('%Y-%m-%d')
        
        # Get fixtures (matches) for the date range
        params = {
            'from': from_date,
            'to': to_date,
            'status': 'NS',  # Not started
            'timezone': 'Europe/London'
        }
        
        fixtures_data = make_api_request('fixtures', params)
        if not fixtures_data or 'response' not in fixtures_data:
            logger.error("No fixtures data received from API")
            return get_sample_matches(start_date, end_date)
        
        matches = []
        for fixture in fixtures_data['response']:
            try:
                # Get odds for this fixture if available
                odds = get_match_odds(fixture['fixture']['id'])
                
                match = {
                    'home_team': fixture['teams']['home']['name'],
                    'away_team': fixture['teams']['away']['name'],
                    'league': fixture['league']['name'],
                    'match_date': parser.parse(fixture['fixture']['date']).strftime('%Y-%m-%d %H:%M'),
                    'over_15_odds': odds.get('over_15', None),
                    'under_15_odds': odds.get('under_15', None),
                    'prediction_confidence': 0  # Will be calculated by the predictor
                }
                matches.append(match)
                
            except Exception as e:
                logger.error(f"Error processing fixture {fixture.get('fixture', {}).get('id')}: {e}")
                continue
        
        return matches
        
    except Exception as e:
        logger.error(f"Error fetching matches: {e}")
        return get_sample_matches(start_date, end_date)

def get_match_odds(fixture_id):
    """Get odds for a specific fixture"""
    params = {'fixture': fixture_id}
    odds_data = make_api_request('odds', params)
    
    if not odds_data or 'response' not in odds_data or not odds_data['response']:
        return {'over_15': None, 'under_15': None}
    
    # Try to find over/under 1.5 goals in the bookmaker odds
    try:
        bookmakers = odds_data['response'][0].get('bookmakers', [])
        for bookmaker in bookmakers:
            if 'bets' in bookmaker:
                for bet in bookmaker['bets']:
                    if bet['id'] == 5:  # Over/Under 1.5 goals
                        for outcome in bet['values']:
                            if outcome['value'] == 'Over 1.5':
                                over_15 = float(outcome['odd'])
                            elif outcome['value'] == 'Under 1.5':
                                under_15 = float(outcome['odd'])
                        
                        return {
                            'over_15': round(over_15, 2) if 'over_15' in locals() else None,
                            'under_15': round(under_15, 2) if 'under_15' in locals() else None
                        }
    except Exception as e:
        logger.error(f"Error parsing odds: {e}")
    
    return {'over_15': None, 'under_15': None}

def get_sample_matches(start_date, end_date):
    """Generate sample matches as fallback when API is not available"""
    matches = []
    current_date = start_date
    
    leagues = ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"]
    teams = ["Arsenal", "Chelsea", "Man Utd", "Liverpool", "Man City", 
             "Barcelona", "Real Madrid", "Atletico", "Sevilla", "Valencia",
             "Juventus", "AC Milan", "Inter", "Napoli", "Roma",
             "Bayern Munich", "Dortmund", "Leipzig", "Leverkusen", "Wolfsburg",
             "PSG", "Lyon", "Marseille", "Monaco", "Lille"]
    
    while current_date <= end_date:
        # Generate 2-5 matches per day
        num_matches = 2 + (current_date.day % 4)  # Vary number of matches
        for _ in range(num_matches):
            home = random.choice(teams)
            away = random.choice([t for t in teams if t != home])
            
            # Generate random odds and prediction confidence
            over_15_odds = round(random.uniform(1.1, 2.5), 2)
            under_15_odds = round(random.uniform(1.1, 3.0), 2)
            
            matches.append({
                'home_team': home,
                'away_team': away,
                'league': random.choice(leagues),
                'match_date': current_date.strftime('%Y-%m-%d %H:%M'),
                'over_15_odds': over_15_odds,
                'under_15_odds': under_15_odds,
                'prediction_confidence': round(random.uniform(50, 95), 1)
            })
        
        current_date += timedelta(days=1)
    
    return matches

# Removed scraping functions as we're using API-Football now
