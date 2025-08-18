import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import os
import logging
from model_loader import get_model, get_scaler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Placeholder for the model and scaler
model = None
scaler = None

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
    """Load a pre-trained model and scaler"""
    global model, scaler
    
    if model is None:
        model = get_model()
    if scaler is None:
        scaler = get_scaler()
    
    return model, scaler

def predict_over_15_goals(over_odds, under_odds):
    """
    Predict the probability of a match having over 1.5 goals.
    
    Args:
        over_odds (float): The odds for over 1.5 goals.
        under_odds (float): The odds for under 1.5 goals.
        
    Returns:
        tuple: A tuple containing:
            - float: Probability of over 1.5 goals (0-1)
            - bool: Whether the fallback method was used
    """
    # Load the model and scaler
    model, scaler = load_model()
    
    # If we don't have a model or scaler, use the fallback method
    if model is None or scaler is None:
        logger.warning("Model or scaler not available, using fallback prediction")
        return _fallback_prediction(over_odds, under_odds), True
    
    try:
        # Calculate the odds ratio
        odds_ratio = over_odds / under_odds if under_odds > 0 else 1.0
        
        # Create feature vector
        features = np.array([[over_odds, under_odds, odds_ratio]])
        
        # Scale features
        features_scaled = scaler.transform(features)
        
        # Make prediction
        prob = model.predict_proba(features_scaled)[0][1]  # Probability of class 1 (over 1.5)
        
        return float(prob), False
    except Exception as e:
        logger.error(f"Error in prediction: {e}", exc_info=True)
        return _fallback_prediction(over_odds, under_odds), True


def _fallback_prediction(over_odds, under_odds):
    """
    Fallback prediction method when the model or scaler is not available.
    
    Args:
        over_odds (float): The odds for over 1.5 goals.
        under_odds (float): The odds for under 1.5 goals.
        
    Returns:
        float: Probability of over 1.5 goals (0-1)
    """
    try:
        # Simple heuristic: if over_odds are lower than under_odds, it's more likely to be over 1.5
        if over_odds < under_odds:
            # More likely to be over 1.5, return a higher probability
            return min(0.8, 1.0 / over_odds)  # Cap at 0.8 for safety
        else:
            # More likely to be under 1.5, return a lower probability
            return max(0.2, 1.0 / under_odds)  # Cap at 0.2 for safety
    except Exception as e:
        logger.error(f"Error in fallback prediction: {e}", exc_info=True)
        return 0.5  # Default to 50% if something goes wrong

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
if __name__ == "__main__":
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        logger.info("No pre-trained model found. Generating training data and training a new model...")
        X, y = generate_training_data()
        train_model(X, y)
    else:
        logger.info("Pre-trained model and scaler found. Loading...")
        model, scaler = load_model()
