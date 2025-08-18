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
API_KEY = os.getenv('FOOTBALL_DATA_API_KEY')  # Changed to football-data.org API key
# BASE_URL = 'https://api.the-odds-api.com'
BASE_URL = 'https://api.football-data.org/v4/'

# Headers for API requests - using football-data.org format
HEADERS = {
    'X-Auth-Token': API_KEY
}

def make_api_request(endpoint, params=None):
    """Helper function to make API requests with error handling"""
    if not API_KEY:
        logger.error("API key not found. Please set FOOTBALL_DATA_API_KEY in your .env file")
        return None
        
    try:
        url = f"{BASE_URL}{endpoint}"
        logger.info(f"Making API request to: {url}")
        logger.info(f"Params: {params}")
        logger.info(f"Headers: { {k: '***' if k == 'X-Auth-Token' else v for k, v in HEADERS.items()} }")
        
        response = requests.get(
            url,
            headers=HEADERS,
            params=params or {},
            timeout=10
        )
        
        # Log the response status and headers
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        # Log response body for debugging (first 500 chars to avoid huge logs)
        try:
            logger.info(f"Response body (truncated): {response.text[:500]}")
        except Exception as e:
            logger.error(f"Error reading response body: {e}")
            
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response headers: {dict(e.response.headers)}")
            try:
                logger.error(f"Error response: {e.response.text}")
            except:
                logger.error("Could not read error response")
        return None

def fetch_matches(start_date, end_date, competition_code='PL'):  # Changed default to 'PL' for Premier League
    """
    Fetch football matches from football-data.org within the specified date range.
    
    Args:
        start_date (datetime): Start date for matches
        end_date (datetime): End date for matches
        competition_code (str): Competition code (default: 'PL' for Premier League)
        
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
        
        # Get matches for the date range
        endpoint = f'competitions/{competition_code}/matches'
        params = {
            'dateFrom': from_date,
            'dateTo': to_date,
            'status': 'SCHEDULED',  # Only get scheduled (future) matches
        }
        
        data = make_api_request(endpoint, params=params)
        
        if not data or 'matches' not in data:
            logger.error("Unexpected API response format. Using sample data.")
            return get_sample_matches(start_date, end_date)
        
        matches = []
        for match_data in data['matches']:
            try:
                match = {
                    'id': match_data['id'],
                    'match_date': parser.parse(match_data['utcDate']).strftime('%Y-%m-%d %H:%M'),
                    'status': match_data['status'],
                    'home_team': match_data['homeTeam']['name'],
                    'away_team': match_data['awayTeam']['name'],
                    'league': f"{data['competition']['name']} {match_data['season']['startDate'][:4]}/{match_data['season']['endDate'][2:4]}",
                    'home_odds': None,
                    'draw_odds': None,
                    'away_odds': None,
                    'over_15_odds': round(random.uniform(1.2, 2.5), 2),  # Add over 1.5 odds
                    'prediction': round(random.uniform(0.1, 0.95), 2),    # Random prediction for now
                    'prediction_confidence': random.randint(30, 95)        # Random confidence for now
                }
                
                # Note: Odds are not available in the free tier of football-data.org
                # We'll generate some sample odds for demonstration
                if random.random() > 0.5:  # 50% chance to generate odds
                    match.update({
                        'home_odds': round(random.uniform(1.5, 4.0), 2),
                        'draw_odds': round(random.uniform(3.0, 4.5), 2),
                        'away_odds': round(random.uniform(2.0, 5.0), 2),
                    })
                
                matches.append(match)
                
            except (KeyError, TypeError) as e:
                logger.error(f"Error processing match: {e}")
                continue
        
        return matches
        
    except Exception as e:
        logger.error(f"Error fetching matches: {e}")
        return get_sample_matches(start_date, end_date)

def get_sample_matches(start_date, end_date):
    """Generate sample matches as fallback when API is not available"""
    logger.info("Generating sample match data")
    
    # Generate matches for the next 7 days
    match_dates = [start_date + timedelta(days=i) for i in range(7)]
    
    # Sample teams and leagues
    teams = [
        'Arsenal', 'Aston Villa', 'Bournemouth', 'Brentford', 'Brighton',
        'Chelsea', 'Crystal Palace', 'Everton', 'Fulham', 'Leeds',
        'Leicester', 'Liverpool', 'Man City', 'Man Utd', 'Newcastle',
        'Nottm Forest', 'Southampton', 'Tottenham', 'West Ham', 'Wolves'
    ]
    
    leagues = [
        'Premier League 2024/25', 'La Liga 2024/25', 'Bundesliga 2024/25',
        'Serie A 2024/25', 'Ligue 1 2024/25'
    ]
    
    matches = []
    for i, match_date in enumerate(match_dates):
        home, away = random.sample(teams, 2)
        
        # Generate some random odds
        home_odds = round(random.uniform(1.5, 4.0), 2)
        draw_odds = round(random.uniform(3.0, 4.5), 2)
        away_odds = round(random.uniform(2.0, 5.0), 2)
        
        # Generate a random prediction
        prediction = random.choice(['H', 'D', 'A'])
        confidence = round(random.uniform(0.6, 0.95), 2)
        
        match = {
            'id': 1000 + i,
            'date': match_date,
            'status': 'SCHEDULED',  # Using football-data.org status
            'home_team': home,
            'away_team': away,
            'league': random.choice(leagues),
            'home_odds': home_odds,
            'draw_odds': draw_odds,
            'away_odds': away_odds,
            'prediction': prediction,
            'confidence': confidence
        }
        
        matches.append(match)
    
    return matches

# Removed scraping functions as we're using API-Football now
