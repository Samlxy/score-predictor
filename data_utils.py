import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import db, Team, Match, Player, Injury, MatchEvent, TeamForm
import os
from typing import Dict, List, Optional, Tuple

class DataImporter:
    def __init__(self, db_uri: str = None):
        """Initialize the data importer with database connection"""
        self.db_uri = db_uri or os.getenv('DATABASE_URL', 'sqlite:///football.db')
        self.engine = create_engine(self.db_uri)
        self.Session = sessionmaker(bind=self.engine)
        
    def import_matches_from_csv(self, file_path: str, league: str, season: str):
        """Import match data from a CSV file"""
        df = pd.read_csv(file_path)
        session = self.Session()
        
        try:
            for _, row in df.iterrows():
                # Get or create teams
                home_team = self._get_or_create_team(session, row['HomeTeam'])
                away_team = self._get_or_create_team(session, row['AwayTeam'])
                
                # Parse match date
                match_date = datetime.strptime(row['Date'], '%d/%m/%Y')
                
                # Create or update match
                match = session.query(Match).filter_by(
                    home_team_id=home_team.id,
                    away_team_id=away_team.id,
                    match_date=match_date
                ).first()
                
                if not match:
                    match = Match(
                        home_team_id=home_team.id,
                        away_team_id=away_team.id,
                        league=league,
                        season=season,
                        match_date=match_date,
                        referee=row.get('Referee')
                    )
                
                # Update match details
                self._update_match_from_row(match, row)
                session.add(match)
                
                # Update team form
                self._update_team_form(session, match, home_team, away_team)
                
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            print(f"Error importing matches: {e}")
            return False
        finally:
            session.close()
    
    def _get_or_create_team(self, session, team_name: str) -> Team:
        """Get or create a team by name"""
        team = session.query(Team).filter_by(name=team_name).first()
        if not team:
            team = Team(name=team_name)
            session.add(team)
            session.commit()
        return team
    
    def _update_match_from_row(self, match: Match, row: pd.Series):
        """Update match statistics from a CSV row"""
        # Basic match results
        match.home_goals = int(row['FTHG'])
        match.away_goals = int(row['FTAG'])
        match.home_halftime_goals = int(row['HTHG'])
        match.away_halftime_goals = int(row['HTAG'])
        
        # Match statistics
        stats_mapping = {
            'HS': 'home_shots', 'AS': 'away_shots',
            'HST': 'home_shots_on_target', 'AST': 'away_shots_on_target',
            'HC': 'home_corners', 'AC': 'away_corners',
            'HF': 'home_fouls', 'AF': 'away_fouls',
            'HY': 'home_yellow_cards', 'AY': 'away_yellow_cards',
            'HR': 'home_red_cards', 'AR': 'away_red_cards'
        }
        
        for col, attr in stats_mapping.items():
            if col in row and not pd.isna(row[col]):
                setattr(match, attr, int(row[col]))
        
        # Betting odds (if available)
        if 'B365>2.5' in row and 'B365<2.5' in row:
            match.over_15_odds = float(row['B365>2.5'])
            match.under_15_odds = float(row['B365<2.5'])
    
    def _update_team_form(self, session, match: Match, home_team: Team, away_team: Team):
        """Update team form statistics after a match"""
        for team, is_home in [(home_team, True), (away_team, False)]:
            team_form = session.query(TeamForm).filter_by(
                team_id=team.id,
                season=match.season,
                competition=match.league
            ).first()
            
            if not team_form:
                team_form = TeamForm(
                    team_id=team.id,
                    season=match.season,
                    competition=match.league
                )
            
            team_form.update_form(match)
            session.add(team_form)

def calculate_additional_features(matches: List[Match]) -> pd.DataFrame:
    """Calculate additional features for model training"""
    features = []
    
    for match in matches:
        # Basic match info
        match_features = {
            'match_id': match.id,
            'home_team': match.home_team_ref.name,
            'away_team': match.away_team_ref.name,
            'league': match.league,
            'season': match.season,
            'date': match.match_date,
            'home_goals': match.home_goals,
            'away_goals': match.away_goals,
            'total_goals': match.total_goals,
            'over_15_goals': match.over_15_goals,
            'over_15_odds': match.over_15_odds,
            'under_15_odds': match.under_15_odds
        }
        
        # Add team form features
        for prefix, team, is_home in [('home', match.home_team_ref, True), 
                                     ('away', match.away_team_ref, False)]:
            form = team.get_form()
            match_features.update({
                f'{prefix}_form': ''.join([m['result'] for m in form]),
                f'{prefix}_form_points': sum(3 if m['result'] == 'W' else 1 if m['result'] == 'D' else 0 
                                          for m in form),
                f'{prefix}_goals_scored': sum(m['home_goals'] if is_home else m['away_goals'] 
                                            for m in form if m.get('home_goals') is not None),
                f'{prefix}_goals_conceded': sum(m['away_goals'] if is_home else m['home_goals'] 
                                              for m in form if m.get('away_goals') is not None)
            })
        
        # Add head-to-head features
        h2h = match.get_head_to_head()
        if h2h:
            h2h_home_wins = sum(1 for m in h2h if m.home_team_id == match.home_team_id and m.home_goals > m.away_goals or 
                               m.away_team_id == match.home_team_id and m.away_goals > m.home_goals)
            h2h_draws = sum(1 for m in h2h if m.home_goals == m.away_goals)
            
            match_features.update({
                'h2h_matches': len(h2h),
                'h2h_home_wins': h2h_home_wins,
                'h2h_draws': h2h_draws,
                'h2h_away_wins': len(h2h) - h2h_home_wins - h2h_draws,
                'h2h_goals_home': sum(m.home_goals if m.home_team_id == match.home_team_id else m.away_goals 
                                    for m in h2h if m.home_team_id == match.home_team_id or m.away_team_id == match.home_team_id),
                'h2h_goals_away': sum(m.away_goals if m.away_team_id == match.away_team_id else m.home_goals 
                                    for m in h2h if m.away_team_id == match.away_team_id or m.home_team_id == match.away_team_id)
            })
        
        features.append(match_features)
    
    return pd.DataFrame(features)
