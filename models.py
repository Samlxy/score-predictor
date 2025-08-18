from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy.ext.hybrid import hybrid_property

db = SQLAlchemy()

# Association table for many-to-many relationship between Team and Player
player_team = db.Table('player_team',
    db.Column('player_id', db.Integer, db.ForeignKey('player.id'), primary_key=True),
    db.Column('team_id', db.Integer, db.ForeignKey('team.id'), primary_key=True),
    db.Column('join_date', db.DateTime, default=datetime.utcnow),
    db.Column('is_active', db.Boolean, default=True)
)

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    short_name = db.Column(db.String(10))
    country = db.Column(db.String(100))
    founded = db.Column(db.Integer)
    venue = db.Column(db.String(200))
    
    # Relationships
    home_matches = db.relationship('Match', foreign_keys='Match.home_team_id', backref='home_team_ref', lazy=True)
    away_matches = db.relationship('Match', foreign_keys='Match.away_team_id', backref='away_team_ref', lazy=True)
    players = db.relationship('Player', secondary=player_team, lazy='subquery',
                            backref=db.backref('teams', lazy=True))
    
    def get_form(self, matches=5):
        """Get team's recent form (last N matches)"""
        recent_matches = Match.query.filter(
            ((Match.home_team_id == self.id) | (Match.away_team_id == self.id)) &
            (Match.match_date < datetime.utcnow()) &
            (Match.home_goals.isnot(None)) &
            (Match.away_goals.isnot(None))
        ).order_by(Match.match_date.desc()).limit(matches).all()
        
        return [{
            'match': f"{m.home_team_ref.name if m.home_team_id == self.id else m.away_team_ref.name} " \
                   f"{m.home_goals if m.home_team_id == self.id else m.away_goals}-" \
                   f"{m.away_goals if m.away_team_id == self.id else m.home_goals} " \
                   f"{'H' if m.home_team_id == self.id else 'A'}",
            'result': 'W' if (m.home_team_id == self.id and m.home_goals > m.away_goals) or \
                             (m.away_team_id == self.id and m.away_goals > m.home_goals) else \
                     'D' if m.home_goals == m.away_goals else 'L',
            'date': m.match_date
        } for m in recent_matches]

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    date_of_birth = db.Column(db.Date)
    nationality = db.Column(db.String(100))
    position = db.Column(db.String(50))
    height = db.Column(db.Integer)  # in cm
    weight = db.Column(db.Integer)  # in kg
    
    # Relationships
    injuries = db.relationship('Injury', backref='player', lazy=True)

class Injury(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    type = db.Column(db.String(100))
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    expected_recovery = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic match info
    home_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    league = db.Column(db.String(200), nullable=False)
    season = db.Column(db.String(20))
    match_date = db.Column(db.DateTime, nullable=False, index=True)
    referee = db.Column(db.String(200))
    venue = db.Column(db.String(200))
    attendance = db.Column(db.Integer)
    
    # Match results
    home_goals = db.Column(db.Integer, nullable=True)
    away_goals = db.Column(db.Integer, nullable=True)
    home_halftime_goals = db.Column(db.Integer)
    away_halftime_goals = db.Column(db.Integer)
    match_status = db.Column(db.String(50))  # FT, HT, Postponed, etc.
    
    # Betting odds
    over_15_odds = db.Column(db.Float, nullable=True)
    under_15_odds = db.Column(db.Float, nullable=True)
    home_win_odds = db.Column(db.Float)
    draw_odds = db.Column(db.Float)
    away_win_odds = db.Column(db.Float)
    
    # Match statistics
    home_possession = db.Column(db.Float)  # Percentage
    away_possession = db.Column(db.Float)  # Percentage
    home_shots = db.Column(db.Integer)
    away_shots = db.Column(db.Integer)
    home_shots_on_target = db.Column(db.Integer)
    away_shots_on_target = db.Column(db.Integer)
    home_corners = db.Column(db.Integer)
    away_corners = db.Column(db.Integer)
    home_fouls = db.Column(db.Integer)
    away_fouls = db.Column(db.Integer)
    home_yellow_cards = db.Column(db.Integer)
    away_yellow_cards = db.Column(db.Integer)
    home_red_cards = db.Column(db.Integer)
    away_red_cards = db.Column(db.Integer)
    
    # Prediction data
    prediction_confidence = db.Column(db.Float, nullable=True)
    prediction_correct = db.Column(db.Boolean)
    
    # Metadata
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_source = db.Column(db.String(100))
    
    # Relationships
    events = db.relationship('MatchEvent', backref='match', lazy=True)
    
    @hybrid_property
    def total_goals(self):
        if self.home_goals is not None and self.away_goals is not None:
            return self.home_goals + self.away_goals
        return None
    
    @hybrid_property
    def over_15_goals(self):
        if self.total_goals is not None:
            return self.total_goals > 1.5
        return None
    
    def to_dict(self):
        return {
            'id': self.id,
            'home_team': self.home_team_ref.name if self.home_team_ref else None,
            'away_team': self.away_team_ref.name if self.away_team_ref else None,
            'home_team_id': self.home_team_id,
            'away_team_id': self.away_team_id,
            'league': self.league,
            'season': self.season,
            'match_date': self.match_date.isoformat(),
            'home_goals': self.home_goals,
            'away_goals': self.away_goals,
            'total_goals': self.total_goals,
            'over_15_goals': self.over_15_goals,
            'over_15_odds': self.over_15_odds,
            'under_15_odds': self.under_15_odds,
            'home_win_odds': self.home_win_odds,
            'draw_odds': self.draw_odds,
            'away_win_odds': self.away_win_odds,
            'prediction_confidence': self.prediction_confidence,
            'match_status': self.match_status,
            'referee': self.referee,
            'venue': self.venue,
            'attendance': self.attendance
        }
    
    def get_head_to_head(self, matches=5):
        """Get head-to-head statistics between the two teams"""
        return Match.query.filter(
            ((Match.home_team_id == self.home_team_id) & (Match.away_team_id == self.away_team_id)) |
            ((Match.home_team_id == self.away_team_id) & (Match.away_team_id == self.home_team_id)),
            Match.match_date < self.match_date,
            Match.home_goals.isnot(None),
            Match.away_goals.isnot(None)
        ).order_by(Match.match_date.desc()).limit(matches).all()

class MatchEvent(db.Model):
    """Tracks key events in a match (goals, cards, substitutions, etc.)"""
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    event_type = db.Column(db.String(50), nullable=False)  # goal, yellow_card, red_card, substitution, etc.
    minute = db.Column(db.Integer)
    description = db.Column(db.Text)
    
    # For goals
    is_penalty = db.Column(db.Boolean, default=False)
    is_own_goal = db.Column(db.Boolean, default=False)
    
    # For substitutions
    player_in_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    player_out_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    
    # For cards
    card_type = db.Column(db.String(20))  # yellow, red, yellow_red
    
    # Relationships
    player = db.relationship('Player', foreign_keys=[player_id])
    team = db.relationship('Team')
    player_in = db.relationship('Player', foreign_keys=[player_in_id])
    player_out = db.relationship('Player', foreign_keys=[player_out_id])

class TeamForm(db.Model):
    """Tracks team form and statistics over time"""
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    season = db.Column(db.String(20))
    competition = db.Column(db.String(100))
    
    # Form statistics (last 5-10 matches)
    form = db.Column(db.String(20))  # e.g., "WWDLW"
    home_form = db.Column(db.String(20))
    away_form = db.Column(db.String(20))
    
    # Attack statistics
    goals_scored = db.Column(db.Integer, default=0)
    goals_conceded = db.Column(db.Integer, default=0)
    shots_per_game = db.Column(db.Float)
    shots_on_target_per_game = db.Column(db.Float)
    
    # Defense statistics
    clean_sheets = db.Column(db.Integer, default=0)
    saves_per_game = db.Column(db.Float)
    
    # Discipline
    yellow_cards = db.Column(db.Integer, default=0)
    red_cards = db.Column(db.Integer, default=0)
    
    # Last updated
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    team = db.relationship('Team', backref=db.backref('form_stats', lazy=True))
    
    def update_form(self, match):
        """Update form based on a match result"""
        if match.home_team_id == self.team_id:
            is_home = True
            goals_for = match.home_goals
            goals_against = match.away_goals
        else:
            is_home = False
            goals_for = match.away_goals
            goals_against = match.home_goals
            
        # Update form string (keep last 5 matches)
        if goals_for > goals_against:
            result = 'W'
        elif goals_for == goals_against:
            result = 'D'
        else:
            result = 'L'
            
        self.form = (result + (self.form or ''))[:5]
        
        if is_home:
            self.home_form = (result + (self.home_form or ''))[:5]
        else:
            self.away_form = (result + (self.away_form or ''))[5]
        
        # Update other statistics
        self.goals_scored += goals_for
        self.goals_conceded += goals_against
        
        if goals_against == 0:
            self.clean_sheets += 1
