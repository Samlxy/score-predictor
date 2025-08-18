import os
import tempfile
import requests
import joblib
from urllib.parse import urlparse
import urllib.request

def load_model_from_url(model_url):
    """
    Load a scikit-learn model from a URL.
    
    Args:
        model_url (str): URL to the model file.
        
    Returns:
        The loaded model.
        
    Raises:
        Exception: If there's an error loading the model.
    """
    try:
        # Create a temporary directory to store the downloaded model
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract the filename from the URL
            parsed_url = urlparse(model_url)
            filename = os.path.basename(parsed_url.path)
            temp_path = os.path.join(temp_dir, filename)
            
            # Download the file
            print(f"Downloading model from {model_url}...")
            urllib.request.urlretrieve(model_url, temp_path)
            
            # Load the model
            print("Loading model...")
            model = joblib.load(temp_path)
            print("Model loaded successfully!")
            return model
    except Exception as e:
        error_msg = f"Error loading model from {model_url}: {e}"
        print(error_msg)
        raise Exception(error_msg) from e

def get_model():
    """
    Get the pre-trained model, downloading it if necessary.
    
    Returns:
        The loaded model or None if loading fails.
    """
    # URL to the model file in GitHub Gist
    model_url = (
        "https://gist.githubusercontent.com/Samlxy/"
        "a1b2c3d4e5f6g7h8i9j0/raw/over_15_goals_model.pkl"
    )
    
    try:
        return load_model_from_url(model_url)
    except Exception as e:
        print(f"Failed to load model: {e}")
        return None

def get_scaler():
    """
    Get the pre-trained scaler, downloading it if necessary.
    
    Returns:
        The loaded scaler or None if loading fails.
    """
    # URL to the scaler file in GitHub Gist
    scaler_url = (
        "https://gist.githubusercontent.com/Samlxy/"
        "a1b2c3d4e5f6g7h8i9j0/raw/scaler.pkl"
    )
    
    try:
        return load_model_from_url(scaler_url)
    except Exception as e:
        print(f"Failed to load scaler: {e}")
        return None
