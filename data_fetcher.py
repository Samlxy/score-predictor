from datetime import datetime, timedelta
import random
import time
from models import Match, db
from scrapers.bet9ja_scraper import get_bet9ja_matches

def fetch_matches(start_date, end_date, use_real_data=True):
    """
    Fetch matches from betting sites within the specified date range.
    
    Args:
        start_date (datetime): Start date for the date range
        end_date (datetime): End date for the date range
        use_real_data (bool): Whether to use real data from betting sites or sample data
        
    Returns:
        list: List of match dictionaries
    """
    if use_real_data:
        try:
            print("Fetching real match data from Bet9ja...")
            matches = get_bet9ja_matches()
            
            # Filter matches by date range
            filtered_matches = []
            for match in matches:
                try:
                    match_time = datetime.fromisoformat(match['match_time'])
                    if start_date <= match_time <= end_date:
                        # Add prediction confidence based on odds
                        if 'over_15_odds' in match and match['over_15_odds']:
                            # Simple conversion from odds to probability (with some randomness for demo)
                            # Lower odds = higher probability of over 1.5 goals
                            prob = 1 / match['over_15_odds']
                            # Add some randomness to make it more interesting
                            match['prediction_confidence'] = min(99, max(1, round(prob * 100 * (0.8 + 0.4 * random.random()))))
                        else:
                            match['prediction_confidence'] = round(random.uniform(30, 70), 1)
                            
                        filtered_matches.append(match)
                except Exception as e:
                    print(f"Error processing match {match.get('home_team', 'Unknown')} vs {match.get('away_team', 'Unknown')}: {e}")
            
            print(f"Found {len(filtered_matches)} matches within the date range.")
            return filtered_matches
            
        except Exception as e:
            print(f"Error fetching real data: {e}")
            print("Falling back to sample data...")
    
    # Fallback to sample data if real data fetch fails or use_real_data is False
    print("Using sample match data...")
    return _generate_sample_matches(start_date, end_date)

def _generate_sample_matches(start_date, end_date):
    """Generate sample match data for testing."""
    matches = []
    current_date = start_date
    
    leagues = ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"]
    teams = ["Arsenal", "Chelsea", "Man Utd", "Liverpool", "Man City", 
             "Barcelona", "Real Madrid", "Atletico", "Sevilla", "Valencia",
             "Juventus", "AC Milan", "Inter", "Napoli", "Roma",
             "Bayern Munich", "Dortmund", "Leipzig", "Leverkusen", "Wolfsburg",
             "PSG", "Lyon", "Marseille", "Monaco", "Lille"]
    
    while current_date <= end_date:
        # Generate 3-8 matches per day
        num_matches = random.randint(3, 8)
        for _ in range(num_matches):
            home = random.choice(teams)
            away = random.choice([t for t in teams if t != home])  # Ensure different teams
            
            # Generate random odds and prediction confidence
            over_15_odds = round(random.uniform(1.1, 2.5), 2)
            under_15_odds = round(random.uniform(1.1, 3.0), 2)
            
            # Calculate prediction confidence based on odds (lower odds = higher confidence)
            prob = 1 / over_15_odds
            prediction_confidence = min(99, max(1, round(prob * 100 * (0.8 + 0.4 * random.random()))))
            
            matches.append({
                'home_team': home,
                'away_team': away,
                'league': random.choice(leagues),
                'match_time': current_date.strftime('%Y-%m-%d %H:%M'),
                'match_date': current_date.strftime('%Y-%m-%d %H:%M'),  # For backward compatibility
                'over_15_odds': over_15_odds,
                'under_15_odds': under_15_odds,
                'prediction_confidence': prediction_confidence,
                'source': 'sample_data'
            })
        
        current_date += timedelta(days=1)
    
    return matches

def scrape_bet9ja_matches():
    """
    Scrape match data from bet9ja.com
    Note: This is a placeholder. In a real implementation, you would need to:
    1. Check bet9ja's terms of service
    2. Use proper headers to avoid being blocked
    3. Handle rate limiting
    4. Parse the HTML structure of their website
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # This URL is an example and may not be correct
        url = "https://www.bet9ja.com/market/over-1.5-goals"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse the HTML response
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract match data (this is a simplified example)
        matches = []
        # Add parsing logic here based on bet9ja's HTML structure
        
        return matches
        
    except Exception as e:
        print(f"Error scraping bet9ja: {e}")
        return []

def scrape_sportybet_matches():
    """
    Scrape match data from sportybet.com
    Note: This is a placeholder. Similar considerations as scrape_bet9ja_matches apply.
    """
    # Implementation would be similar to scrape_bet9ja_matches
    return []
