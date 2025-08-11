# Soccer Predictor - Over 1.5 Goals

A web application that predicts soccer matches likely to have over 1.5 goals based on historical data and betting odds.

## Features

- Fetches match data (currently using sample data)
- Predicts probability of over 1.5 goals
- Displays matches in a sortable table with color-coded confidence levels
- Filter matches by date range
- Responsive design for mobile and desktop

## Setup

1. Clone the repository
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
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
