# Soccer Predictor - Over 1.5 Goals

A web application that predicts soccer matches likely to have over 1.5 goals based on historical data and betting odds.

## How the over 1.5 goals prediction works in this application:
### 1. Core Prediction Function:
- The main prediction is handled by the 
predict_over_15_goals()
 function in predictor.py
- It uses a machine learning model (RandomForestClassifier) to predict the probability of a match having over 1.5 goals

### 2. Input Features:
- The model uses several key inputs:
  - over_15_odds: The betting odds for over 1.5 goals
  - under_15_odds: The betting odds for under 1.5 goals
  - odds_ratio: A calculated ratio of over_odds/under_odds

### 3. Model Training:
- The model is trained using historical match data (currently using data from ```football-data.org``` in the code)
- It learns patterns between the betting odds and actual match outcomes
- The training data includes features like over/under odds and the actual outcome (over/under 1.5 goals)

### 4. Prediction Logic:
- For each match, the function:
  - Extracts the over/under 1.5 odds
  - Calculates the odds ratio
  - Feeds these into the trained model
  - Returns a probability between 0 and 1 (where 1 = 100% confidence in over 1.5 goals)

### 5. Confidence Levels:
- The UI displays predictions with color-coded confidence levels:
  - High confidence (green): ≥ 70% probability
  - Medium confidence (yellow): 40-70% probability
  - Low confidence (red): < 40% probability

### 6. Fallback Mechanism:
- If the model isn't available, it uses a simple heuristic based on the odds:
  - If over_odds are ≤ 1.5, it predicts high probability (80%)
  - Otherwise, it calculates a probability based on the odds
    
### 7. The system is designed to be flexible - you could improve it by:
- Adding more historical match data
- Including additional features like team form, head-to-head statistics, or player availability
- Implementing more sophisticated machine learning models

## Features

- Fetches match data from football-data.org
- Predicts probability of over 1.5 goals
- Displays matches in a sortable table with color-coded confidence levels
- Filter matches by leagues and by date range
- Responsive design for mobile and desktop

## Setup

1. Clone the repository
2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python app.py
   ```
4. Open your browser and navigate to `http://127.0.0.1:5000`

## Data Sources

- Currently uses sample data
- Can be extended to fetch real data from betting sites like bet9ja.com or sportybet.com

## Future Improvements

- Add real data scraping from betting sites
- Implement user accounts to save favorite matches
- Add more prediction models and statistics
- Include head-to-head history between teams
- Add email notifications for high-confidence predictions

## Disclaimer

This application is for informational purposes only. Gambling can be addictive. Please gamble responsibly and only bet what you can afford to lose.
