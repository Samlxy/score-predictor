from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    home_team = db.Column(db.String(200), nullable=False)
    away_team = db.Column(db.String(200), nullable=False)
    league = db.Column(db.String(200), nullable=False)
    match_date = db.Column(db.DateTime, nullable=False)
    home_goals = db.Column(db.Integer, nullable=True)
    away_goals = db.Column(db.Integer, nullable=True)
    over_15_odds = db.Column(db.Float, nullable=True)
    under_15_odds = db.Column(db.Float, nullable=True)
    prediction_confidence = db.Column(db.Float, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'home_team': self.home_team,
            'away_team': self.away_team,
            'league': self.league,
            'match_date': self.match_date.isoformat(),
            'home_goals': self.home_goals,
            'away_goals': self.away_goals,
            'over_15_odds': self.over_15_odds,
            'under_15_odds': self.under_15_odds,
            'prediction_confidence': self.prediction_confidence
        }
