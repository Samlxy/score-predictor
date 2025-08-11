from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import os
from models import db, Match
from data_fetcher import fetch_matches
from predictor import predict_over_15_goals

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///soccer_predictions.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    return app

app = create_app()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        # Convert string dates to datetime objects
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Fetch matches and make predictions
        matches = fetch_matches(start_date, end_date)
        matches_with_predictions = []
        
        for match in matches:
            # Get prediction for over 1.5 goals
            prediction = predict_over_15_goals(match)
            match['prediction'] = prediction
            matches_with_predictions.append(match)
        
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
    
    # Default date range: next 7 days
    default_start = datetime.now().strftime('%Y-%m-%d')
    default_end = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    
    return render_template('index.html', 
                         start_date=default_start,
                         end_date=default_end)

if __name__ == '__main__':
    app.run(debug=True)
