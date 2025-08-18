from flask import Flask, render_template, request, jsonify, flash
from datetime import datetime, timedelta
import os
import logging
from dotenv import load_dotenv
from models import db, Match
from data_fetcher import fetch_matches
from predictor import predict_over_15_goals

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///soccer_predictor.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-123')
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    return app

app = create_app()

@app.route('/', methods=['GET', 'POST'])
def index():
    # Default values
    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)
    competition_code = 'PL'  # Default to Premier League
    matches = []
    
    if request.method == 'POST':
        try:
            # Get form data
            start_date_str = request.form.get('start_date')
            end_date_str = request.form.get('end_date')
            competition_code = request.form.get('competition_code', competition_code)
            
            # Convert string dates to datetime objects
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            
            # Validate date range
            if end_date < start_date:
                flash('End date must be after start date', 'error')
                end_date = start_date + timedelta(days=7)
            if (end_date - start_date).days > 30:
                flash('Date range cannot exceed 30 days', 'warning')
                end_date = start_date + timedelta(days=30)
            
            # Fetch matches with the selected parameters
            logger.info(f"Fetching matches from {start_date} to {end_date} for competition {competition_code}")
            matches = fetch_matches(start_date, end_date, competition_code)
            
            if not matches:
                flash('No matches found for the selected date range and league', 'info')
            else:
                # Process matches with predictions
                matches_with_predictions = process_matches(matches)
                matches = sorted(matches_with_predictions, 
                              key=lambda x: (get_confidence_level(x['prediction']), 
                                           -x['prediction']))
            
        except ValueError as e:
            logger.error(f"Error processing form data: {e}")
            flash('Invalid input. Please check your selections and try again.', 'error')
        except Exception as e:
            logger.error(f"Error fetching matches: {e}")
            flash('An error occurred while fetching matches. Please try again later.', 'error')
    
    # Render the template with the current form values and matches
    return render_template(
        'index.html',
        start_date=start_date,
        end_date=end_date,
        competition_code=competition_code,
        matches=matches or []
    )

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

def get_confidence_level(prediction):
    """Helper function to determine confidence level based on prediction value."""
    if prediction >= 0.7:  # High confidence
        return 0
    elif prediction >= 0.4:  # Medium confidence
        return 1
    return 2  # Low confidence

def process_matches(matches):
    """Process matches to add predictions and confidence scores."""
    processed_matches = []
    for match in matches:
        try:
            # Get prediction for over 1.5 goals
            prediction = predict_over_15_goals(match)
            match['prediction'] = prediction
            match['prediction_confidence'] = round(prediction * 100, 1)  # Convert to percentage
            processed_matches.append(match)
        except Exception as e:
            logger.error(f"Error processing match {match.get('home_team', 'Unknown')} vs {match.get('away_team', 'Unknown')}: {e}")
            continue
    return processed_matches

if __name__ == '__main__':
    app.run(debug=True)
