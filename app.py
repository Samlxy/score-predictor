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
    try:
        if request.method == 'POST':
            start_date_str = request.form.get('start_date')
            end_date_str = request.form.get('end_date')
            
            try:
                # Convert string dates to datetime objects
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                
                # Validate date range
                if end_date < start_date:
                    flash('End date must be after start date', 'error')
                    end_date = start_date + timedelta(days=7)
                if (end_date - start_date).days > 30:
                    flash('Date range cannot exceed 30 days', 'warning')
                    end_date = start_date + timedelta(days=30)
                
                # Fetch matches and make predictions
                logger.info(f"Fetching matches from {start_date} to {end_date}")
                matches = fetch_matches(start_date, end_date)
                
                if not matches:
                    flash('No matches found for the selected date range', 'info')
                
                matches_with_predictions = []
                for match in matches:
                    try:
                        # Get prediction for over 1.5 goals
                        prediction = predict_over_15_goals(match)
                        match['prediction'] = prediction
                        match['prediction_confidence'] = round(prediction * 100, 1)  # Convert to percentage
                        matches_with_predictions.append(match)
                    except Exception as e:
                        logger.error(f"Error processing match {match.get('home_team', 'Unknown')} vs {match.get('away_team', 'Unknown')}: {e}")
                        continue
                
                # Sort by confidence level (high > medium > low) and then by prediction percentage
                def get_confidence_level(prediction):
                    if prediction >= 0.7:  # High confidence
                        return 0
                    elif prediction >= 0.4:  # Medium confidence
                        return 1
                    else:  # Low confidence
                        return 2
                
                matches_with_predictions.sort(key=lambda x: (get_confidence_level(x['prediction']), -x['prediction']))
                
                return render_template('index.html', 
                                    matches=matches_with_predictions,
                                    start_date=start_date.strftime('%Y-%m-%d'),
                                    end_date=end_date.strftime('%Y-%m-%d'))
                
            except ValueError as e:
                logger.error(f"Date parsing error: {e}")
                flash('Invalid date format. Please use YYYY-MM-DD format.', 'error')
            except Exception as e:
                logger.error(f"Error fetching matches: {e}")
                flash('An error occurred while fetching matches. Using sample data instead.', 'error')
        
        # Default date range: next 7 days
        default_start = datetime.now()
        default_end = default_start + timedelta(days=7)
        
        return render_template('index.html',
                            start_date=default_start.strftime('%Y-%m-%d'),
                            end_date=default_end.strftime('%Y-%m-%d'))
    
    except Exception as e:
        logger.error(f"Unexpected error in index route: {e}")
        flash('An unexpected error occurred. Please try again later.', 'error')
        return render_template('index.html',
                            start_date=datetime.now().strftime('%Y-%m-%d'),
                            end_date=(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'))

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

if __name__ == '__main__':
    app.run(debug=True)
