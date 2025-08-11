import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import re

class Bet9jaScraper:
    def __init__(self):
        self.base_url = "https://www.bet9ja.com/"
        self.matches = []
        self.setup_driver()
    
    def setup_driver(self):
        """Set up the Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        # Run in headless mode with additional arguments
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Set up Chrome driver with retry mechanism
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()),
                    options=chrome_options
                )
                # Set page load and script timeouts
                self.driver.set_page_load_timeout(30)
                self.driver.set_script_timeout(30)
                # Execute CDP commands to pass as a real browser
                self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"})
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                print(f"Attempt {attempt + 1} failed, retrying...")
                time.sleep(2)
    
    def close(self):
        """Close the WebDriver."""
        if hasattr(self, 'driver'):
            self.driver.quit()
    
    def get_matches(self):
        """
        Navigate to the main page and extract match information.
        
        Returns:
            list: List of dictionaries containing match information
        """
        try:
            print("Navigating to Bet9ja...")
            # First, try to access the football page directly
            football_url = f"{self.base_url}football"
            self.driver.get(football_url)
            
            # Wait for dynamic content to load
            time.sleep(5)  # Initial wait for dynamic content
            
            # Try to find matches with a more flexible approach
            try:
                # Wait for any match element to be present
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".ev-matches, .event, .match-row, [class*='match'], [id*='match']"))
                )
                print("Found match elements, extracting data...")
            except Exception as e:
                print(f"Could not find match elements: {e}")
                # Take a screenshot for debugging
                self.driver.save_screenshot("bet9ja_debug.png")
                print("Screenshot saved as bet9ja_debug.png")
            
            # Extract match data
            matches = self.extract_match_data()
            print(f"Found {len(matches)} matches")
            return matches
            
        except Exception as e:
            print(f"Error getting matches: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
        
    def extract_match_data(self):
        """Extract match data from the current page."""
        matches = []
        
        try:
            # Try multiple possible selectors for match rows
            possible_selectors = [
                ".event-row", 
                ".ev-matches", 
                ".match", 
                ".event",
                "[class*='match']",
                "[class*='event']",
                "div[class^='event']",
                "div[class*='match']"
            ]
            
            match_rows = []
            for selector in possible_selectors:
                try:
                    match_rows = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                    )
                    if match_rows:
                        print(f"Found {len(match_rows)} matches using selector: {selector}")
                        break
                except:
                    continue
            
            if not match_rows:
                print("No match rows found with any selector")
                return []
            
            print(f"Found {len(match_rows)} match rows to process")
            
            for row in match_rows:
                try:
                    # Try to get team names using multiple possible selectors
                    home_team, away_team = "", ""
                    team_selectors = [
                        (".team-home, .home-team, [class*='home']", ".team-away, .away-team, [class*='away']"),
                        ("div:first-child > a", "div:last-child > a"),
                        ("a:first-child", "a:last-child")
                    ]
                    
                    for home_sel, away_sel in team_selectors:
                        try:
                            home_elem = row.find_element(By.CSS_SELECTOR, home_sel)
                            away_elem = row.find_element(By.CSS_SELECTOR, away_sel)
                            home_team = home_elem.text.strip()
                            away_team = away_elem.text.strip()
                            if home_team and away_team:
                                break
                        except:
                            continue
                    
                    # Skip if we couldn't get team names
                    if not home_team or not away_team:
                        continue
                        
                    # Extract league - try multiple selectors
                    league = "Unknown League"
                    league_selectors = [
                        ".league-name, .competition, [class*='league'], [class*='comp']",
                        "div:first-child",
                        "div:first-of-type"
                    ]
                    
                    for selector in league_selectors:
                        try:
                            league_elem = row.find_element(By.CSS_SELECTOR, selector)
                            league = league_elem.text.strip()
                            if league and league.lower() != home_team.lower() and league.lower() != away_team.lower():
                                break
                        except:
                            continue
                    
                    # Extract time - try multiple selectors
                    match_time = datetime.utcnow().isoformat()
                    time_selectors = [
                        "[class*='time'], [class*='date'], [class*='kickoff']",
                        "div:last-child"
                    ]
                    
                    for selector in time_selectors:
                        try:
                            time_elem = row.find_element(By.CSS_SELECTOR, selector)
                            time_str = time_elem.text.strip()
                            if time_str:
                                parsed_time = self.parse_match_time(time_str)
                                if parsed_time:
                                    match_time = parsed_time
                                    break
                        except:
                            continue
                    
                    # Extract odds - try multiple patterns
                    over_15_odds = None
                    odds_selectors = [
                        ("[class*='odds']", "1.5"),
                        ("[class*='over']", "1.5"),
                        ("div:contains('1.5')", "1.5"),
                        ("div", "1.5")
                    ]
                    
                    for selector, odds_type in odds_selectors:
                        try:
                            odds_elems = row.find_elements(By.CSS_SELECTOR, selector)
                            for elem in odds_elems:
                                text = elem.text.strip()
                                if odds_type in text and any(c.isdigit() for c in text):
                                    try:
                                        # Try to extract the first number that looks like odds
                                        import re
                                        numbers = re.findall(r'\d+\.?\d*', text)
                                        if numbers:
                                            over_15_odds = float(numbers[0])
                                            break
                                    except (ValueError, IndexError):
                                        continue
                            if over_15_odds is not None:
                                break
                        except:
                            continue
                    
                    if not home_team or not away_team or not match_time:
                        continue
                        
                    match_data = {
                        'home_team': home_team,
                        'away_team': away_team,
                        'league': league,
                        'match_time': match_time,
                        'over_15_odds': over_15_odds,
                        'source': 'bet9ja',
                        'last_updated': datetime.utcnow().isoformat()
                    }
                    
                    matches.append(match_data)
                    
                except Exception as e:
                    print(f"Error extracting match data: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error in extract_match_data: {e}")
        
        return matches
    
    def parse_match_time(self, time_str):
        """Parse match time string into a datetime object."""
        try:
            # Handle different time formats
            time_str = time_str.lower().strip()
            now = datetime.now()
            
            # Handle 'Today, HH:MM' format
            if 'today' in time_str:
                time_part = time_str.replace('today', '').strip()
                match_time = datetime.strptime(time_part, '%H:%M')
                return now.replace(hour=match_time.hour, minute=match_time.minute, second=0, microsecond=0).isoformat()
            
            # Handle 'Tomorrow, HH:MM' format
            elif 'tomorrow' in time_str:
                time_part = time_str.replace('tomorrow', '').strip()
                match_time = datetime.strptime(time_part, '%H:%M')
                return (now + timedelta(days=1)).replace(hour=match_time.hour, minute=match_time.minute, second=0, microsecond=0).isoformat()
            
            # Handle 'DD/MM HH:MM' format
            elif re.match(r'\d{2}/\d{2} \d{2}:\d{2}', time_str):
                match_time = datetime.strptime(time_str, '%d/%m %H:%M')
                # Assume current year
                match_time = match_time.replace(year=now.year)
                # If the date has already passed this year, assume it's for next year
                if match_time < now:
                    match_time = match_time.replace(year=now.year + 1)
                return match_time.isoformat()
            
            # Handle 'In Xh Ymin' format (live or upcoming)
            elif 'in' in time_str and ('h' in time_str or 'min' in time_str):
                return now.isoformat()  # Return current time as an approximation
            
            # Default to current time if format is not recognized
            return now.isoformat()
            
        except Exception as e:
            print(f"Error parsing time '{time_str}': {e}")
            return datetime.utcnow().isoformat()

def get_bet9ja_matches():
    """Convenience function to get matches from Bet9ja."""
    scraper = None
    try:
        scraper = Bet9jaScraper()
        return scraper.get_matches()
    except Exception as e:
        print(f"Error in get_bet9ja_matches: {e}")
        return []
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    matches = get_bet9ja_matches()
    print(f"Found {len(matches)} matches:")
    for match in matches:
        print(f"{match['home_team']} vs {match['away_team']} - {match['league']} - {match.get('over_15_odds', 'N/A')}")
