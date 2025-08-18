import os
import tempfile
import requests
import joblib
from urllib.parse import urlparse, parse_qs
import urllib.request
import gdown  # For downloading from Google Drive

def download_from_google_drive(url, output_path):
    """
    Download a file from Google Drive.
    
    Args:
        url (str): The Google Drive URL or file ID.
        output_path (str): The path where the file should be saved.
        
    Returns:
        str: The path to the downloaded file.
    """
    try:
        # If URL is a Google Drive shareable link, extract the file ID
        if 'drive.google.com' in url:
            # Extract file ID from Google Drive URL
            parsed_url = urlparse(url)
            if 'id=' in parsed_url.query:
                file_id = parse_qs(parsed_url.query)['id'][0]
            else:
                # Handle URL format: https://drive.google.com/file/d/FILE_ID/view
                file_id = parsed_url.path.split('/')[3]
            
            # Construct the download URL
            url = f'https://drive.google.com/uc?id={file_id}'
        else:
            # Assume it's already a direct download link
            file_id = url
        
        # Download the file using gdown
        gdown.download(url, output_path, quiet=False)
        return output_path
    except Exception as e:
        error_msg = f"Error downloading file from Google Drive: {e}"
        print(error_msg)
        raise Exception(error_msg) from e

def load_model_from_file(file_path):
    """
    Load a scikit-learn model from a file.
    
    Args:
        file_path (str): Path to the model file.
        
    Returns:
        The loaded model.
        
    Raises:
        Exception: If there's an error loading the model.
    """
    try:
        print(f"Loading model from {file_path}...")
        model = joblib.load(file_path)
        print("Model loaded successfully!")
        return model
    except Exception as e:
        error_msg = f"Error loading model from {file_path}: {e}"
        print(error_msg)
        raise Exception(error_msg) from e

def get_model():
    """
    Get the pre-trained model, downloading it from Google Drive if necessary.
    
    Returns:
        The loaded model or None if loading fails.
    """
    # Google Drive file ID for the model
    model_file_id = "1k7-3aVjXb8Qe5y8z9x0cVbNm2pOqRsTd"  # Over 1.5 goals model
    model_url = f"https://drive.google.com/file/d/{model_file_id}/view?usp=sharing"
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download the model file
            model_path = os.path.join(temp_dir, "over_15_goals_model.pkl")
            download_from_google_drive(model_url, model_path)
            
            # Load the model
            return load_model_from_file(model_path)
    except Exception as e:
        print(f"Failed to load model: {e}")
        return None

def get_scaler():
    """
    Get the pre-trained scaler, downloading it from Google Drive if necessary.
    
    Returns:
        The loaded scaler or None if loading fails.
    """
    # Google Drive file ID for the scaler
    scaler_file_id = "1k8-4bWkY9cX0a1b2cD3eF4gH5iJ6kL7mN"  # Scaler file
    scaler_url = f"https://drive.google.com/file/d/{scaler_file_id}/view?usp=sharing"
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download the scaler file
            scaler_path = os.path.join(temp_dir, "scaler.pkl")
            download_from_google_drive(scaler_url, scaler_path)
            
            # Load the scaler
            return load_model_from_file(scaler_path)
    except Exception as e:
        print(f"Failed to load scaler: {e}")
        return None
