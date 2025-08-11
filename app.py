from flask import Flask, render_template, request, jsonify, flash
from datetime import datetime, timedelta
import os
from models import db, Match
from data_fetcher import fetch_matches
from predictor import predict_over_15_goals
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///soccer_predictions.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Set a secret key for session management
    # In production, use a more secure method to store this key (e.g., environment variables)
    app.secret_key = 'your-secret-key-here-12345'  # Change this to a secure random key in production
    
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
            use_real_data = request.form.get('use_real_data', 'false').lower() == 'true'
            
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
                logger.info(f"Fetching matches from {start_date} to {end_date} (real data: {use_real_data})")
                matches = fetch_matches(start_date, end_date, use_real_data=use_real_data)
                
                if not matches:
                    flash('No matches found for the selected date range', 'info')
                
                # Process matches and add predictions
                matches_with_predictions = []
                for match in matches:
                    try:
                        # Get prediction for over 1.5 goals
                        prediction = predict_over_15_goals(match)
                        match['prediction'] = prediction
                        
                        # Ensure all required fields are present
                        match.setdefault('over_15_odds', None)
                        match.setdefault('under_15_odds', None)
                        match.setdefault('league', 'Unknown League')
                        match.setdefault('source', 'Unknown Source')
                        
                        matches_with_predictions.append(match)
                    except Exception as e:
                        logger.error(f"Error processing match {match.get('home_team', 'Unknown')} vs {match.get('away_team', 'Unknown')}: {e}")
                        continue
                
                # Sort by prediction confidence percentage in descending order
                matches_with_predictions.sort(key=lambda x: -x['prediction'])
                
                return render_template('index.html', 
                                    matches=matches_with_predictions,
                                    start_date=start_date.strftime('%Y-%m-%d'),
                                    end_date=end_date.strftime('%Y-%m-%d'),
                                    use_real_data=use_real_data)
                
            except ValueError as e:
                logger.error(f"Date parsing error: {e}")
                flash('Invalid date format. Please use YYYY-MM-DD format.', 'error')
            except Exception as e:
                logger.error(f"Error fetching matches: {e}")
                flash('An error occurred while fetching matches. Using sample data instead.', 'error')
                return render_template('index.html',
                                    start_date=start_date_str,
                                    end_date=end_date_str,
                                    use_real_data=False)
        
        # Default date range: next 7 days
        default_start = datetime.now()
        default_end = default_start + timedelta(days=7)
        
        return render_template('index.html', 
                            start_date=default_start.strftime('%Y-%m-%d'),
                            end_date=default_end.strftime('%Y-%m-%d'),
                            use_real_data=False)
    
    except Exception as e:
        logger.error(f"Unexpected error in index route: {e}")
        flash('An unexpected error occurred. Please try again later.', 'error')
        return render_template('index.html',
                            start_date=datetime.now().strftime('%Y-%m-%d'),
                            end_date=(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                            use_real_data=False)

if __name__ == '__main__':
    app.run(debug=True)
