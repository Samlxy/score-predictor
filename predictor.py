import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import os

# Placeholder for the model
model = None
scaler = None
MODEL_PATH = 'over_15_goals_model.pkl'
SCALER_PATH = 'scaler.pkl'

def train_model(X, y):
    """
    Train a model to predict over 1.5 goals
    In a real implementation, this would use historical match data
    """
    global model, scaler
    
    # Scale the features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train a simple model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_scaled, y)
    
    # Save the model and scaler
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    
    return model, scaler

def load_model():
    """Load a pre-trained model and scaler if they exist"""
    global model, scaler
    
    if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
        model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
    
    return model, scaler

def predict_over_15_goals(match):
    """
    Predict the probability of over 1.5 goals in a match
    
    Args:
        match (dict): Match data including teams, odds, etc.
        
    Returns:
        float: Probability of over 1.5 goals (0-1)
    """
    global model, scaler
    
    # Load model if not already loaded
    if model is None or scaler is None:
        model, scaler = load_model()
    
    # If no model exists, return a simple prediction based on odds
    if model is None or scaler is None:
        # Simple heuristic: higher odds for over 1.5 means lower probability
        if 'over_15_odds' in match and match['over_15_odds']:
            # Convert odds to implied probability
            prob = 1 / match['over_15_odds']
            # Add some randomness for demo purposes
            prob = min(0.95, max(0.05, prob * (0.9 + 0.2 * np.random.random())))
            return prob
        return 0.5  # Default to 50% if no odds available
    
    # In a real implementation, we would extract features from the match data
    # For now, we'll use a simple approach based on odds
    try:
        # Example features: odds for over 1.5, odds for under 1.5, their ratio
        over_odds = match.get('over_15_odds', 1.8)
        under_odds = match.get('under_15_odds', 2.0)
        
        # Simple feature engineering
        odds_ratio = over_odds / under_odds if under_odds > 0 else 1.0
        
        # Create feature vector
        features = np.array([[over_odds, under_odds, odds_ratio]])
        
        # Scale features
        features_scaled = scaler.transform(features)
        
        # Make prediction
        prob = model.predict_proba(features_scaled)[0][1]  # Probability of class 1 (over 1.5)
        
        return float(prob)
    except Exception as e:
        print(f"Error in prediction: {e}")
        return 0.5  # Fallback to 50% probability

def generate_training_data():
    """
    Generate synthetic training data for demonstration
    In a real implementation, this would use historical match data
    """
    np.random.seed(42)
    
    # Generate random odds and outcomes
    n_samples = 1000
    over_odds = np.random.uniform(1.1, 3.0, n_samples)
    under_odds = np.random.uniform(1.1, 3.0, n_samples)
    
    # Generate synthetic outcomes (1 if over 1.5 goals, 0 otherwise)
    # Higher odds for over 1.5 should correlate with lower probability
    probs = 1.0 / over_odds
    outcomes = (np.random.random(n_samples) < probs).astype(int)
    
    # Create feature matrix
    odds_ratio = over_odds / under_odds
    X = np.column_stack((over_odds, under_odds, odds_ratio))
    
    return X, outcomes

# Initialize with some training data if no model exists
if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
    X, y = generate_training_data()
    train_model(X, y)
