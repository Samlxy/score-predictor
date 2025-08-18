from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime, timedelta
import os
import logging
import sys
from dotenv import load_dotenv
from models import db, Match
from data_fetcher import fetch_matches
from predictor import predict_over_15_goals, load_model

# Initialize model and scaler when the app starts
model_loaded = False
model_load_error = None

def initialize_models():
    """Initialize the ML model and scaler when the app starts."""
    global model_loaded, model_load_error
    try:
        model, scaler = load_model()
        if model is None or scaler is None:
            model_load_error = "Failed to load model or scaler. Using fallback prediction method."
            logger.error(model_load_error)
        else:
            model_loaded = True
            logger.info("Successfully loaded ML model and scaler")
    except Exception as e:
        model_load_error = f"Error initializing model: {str(e)}"
        logger.error(model_load_error, exc_info=True)

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
    
    # Initialize ML models
    initialize_models()
    
    return app

app = create_app()

@app.route('/', methods=['GET', 'POST'])
def index():
    # Default values
    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)
    competition_code = 'PL'  # Default to Premier League
    matches = []
    
    # Show model loading status to the user
    if not model_loaded and model_load_error:
        flash(f'Warning: {model_load_error}', 'warning')
    
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
    """
    Helper function to determine confidence level based on prediction value.
    
    Args:
        prediction (float): The prediction probability (0-1)
        
    Returns:
        str: 'high', 'medium', or 'low' confidence
    """
    if not isinstance(prediction, (int, float)):
        return 'low'
        
    if prediction > 0.8 or prediction < 0.2:
        return 'high'  # High confidence
    elif prediction > 0.7 or prediction < 0.3:
        return 'medium'  # Medium confidence
    return 'low'  # Low confidence

def process_matches(matches):
    """Process matches to add predictions and confidence scores.
    
    Args:
        matches (list): List of match dictionaries containing odds data.
        
    Returns:
        list: List of match dictionaries with added prediction and confidence data.
    """
    for match in matches:
        # Get the prediction for the match
        try:
            over_odds = match.get('over_15_odds', 1.8)  # Default fallback odds
            under_odds = match.get('under_15_odds', 2.0)  # Default fallback odds
            
            # Get prediction and whether fallback was used
            prediction, used_fallback = predict_over_15_goals(over_odds, under_odds)
            
            # Store prediction and confidence
            match['prediction'] = prediction
            match['confidence'] = get_confidence_level(prediction)
            
            # Log if fallback was used
            if used_fallback:
                logger.warning(
                    f"Used fallback prediction for match {match.get('id', 'unknown')}. "
                    f"Odds: over={over_odds}, under={under_odds}, prediction={prediction}"
                )
                
        except Exception as e:
            logger.error(f"Error predicting for match {match.get('id', 'unknown')}: {e}", exc_info=True)
            # Default to 50% prediction if something goes wrong
            match['prediction'] = 0.5
            match['confidence'] = 'low'
    
    return matches

if __name__ == '__main__':
    app.run(debug=True)
