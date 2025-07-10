import pandas as pd
import joblib
from tensorflow.keras.models import load_model
from django.conf import settings
import os
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
import numpy as np

# Global dictionary to store loaded models and preprocessors
MODELS = {
    'temp': {
        'model_path': os.path.join(settings.BASE_DIR, 'sensor', 'models', 'temp_predictor.keras'),
        'preprocessor_path': os.path.join(settings.BASE_DIR, 'sensor', 'models', 'temp_preprocessor.pkl'),
        'model': None,
        'preprocessor': None
    },
    'hum': {
        'model_path': os.path.join(settings.BASE_DIR, 'sensor', 'models', 'hum_predictor.keras'),
        'preprocessor_path': os.path.join(settings.BASE_DIR, 'sensor', 'models', 'hum_preprocessor.pkl'),
        'model': None,
        'preprocessor': None
    },
    'light': {
        'model_path': os.path.join(settings.BASE_DIR, 'sensor', 'models', 'light_predictor.keras'),
        'preprocessor_path': os.path.join(settings.BASE_DIR, 'sensor', 'models', 'light_preprocessor.pkl'),
        'model': None,
        'preprocessor': None
    },
    'snd': {
        'model_path': os.path.join(settings.BASE_DIR, 'sensor', 'models', 'snd_predictor.keras'),
        'preprocessor_path': os.path.join(settings.BASE_DIR, 'sensor', 'models', 'snd_preprocessor.pkl'),
        'model': None,
        'preprocessor': None
    }
}

def load_all_models():
    """Load all models and preprocessors into memory"""
    import sklearn
    print(f"Current scikit-learn version: {sklearn.__version__}")
    
    for target in MODELS.keys():
        try:
            print(f"Loading {target} model...")
            MODELS[target]['model'] = load_model(MODELS[target]['model_path'])
            print(f"Loading {target} preprocessor...")
            MODELS[target]['preprocessor'] = joblib.load(MODELS[target]['preprocessor_path'])
            print(f"Successfully loaded {target} model and preprocessor")
        except Exception as e:
            print(f"Error loading {target} model: {str(e)}")
            import traceback
            traceback.print_exc()

def predict_value(node_id, loc, target, input_data):
    """
    Predict a sensor value based on input data
    
    Args:
        node_id (str): Sensor node ID
        loc (str): Location
        target (str): One of 'temp', 'hum', 'light', 'snd'
        input_data (dict): Dictionary with other sensor values
        
    Returns:
        float: Predicted value
    """
    if target not in MODELS or not MODELS[target]['model']:
        raise ValueError(f"Model for {target} not loaded")
    
    # Create input DataFrame
    input_df = pd.DataFrame({
        'node_id': [node_id],
        'loc': [loc],
        **input_data
    })
    
    # Preprocess input
    processed_input = MODELS[target]['preprocessor'].transform(input_df).toarray()
    
    # Predict
    prediction = MODELS[target]['model'].predict(processed_input, verbose=0)
    return float(prediction[0][0])

def predict_for_time_range(node_id, loc, target, start_date, end_date):
    """
    Predict values for a time range by using historical data patterns
    
    Args:
        node_id (str): Sensor node ID
        loc (str): Location
        target (str): One of 'temp', 'hum', 'light', 'snd'
        start_date (datetime): Start of prediction period
        end_date (datetime): End of prediction period
        
    Returns:
        list: List of dictionaries with timestamp and predicted value
    """
    from .models import Event
    import datetime
    
    # Get historical data for this node/location to establish patterns
    historical_data = Event.objects.filter(
        node_id=node_id,
        loc=loc,
        date_created__gte=start_date - datetime.timedelta(days=30),
        date_created__lte=end_date - datetime.timedelta(days=30)
    ).order_by('date_created')
    
    if not historical_data:
        raise ValueError("No historical data available for pattern recognition")
    
    predictions = []
    current_date = start_date
    
    while current_date <= end_date:
        # Find similar time in historical data (e.g., same hour of day)
        similar_times = [d for d in historical_data 
                        if d.date_created.hour == current_date.hour 
                        and d.date_created.minute == current_date.minute]
        
        if similar_times:
            # Use the average of similar historical readings as input
            avg_input = {
                'temp': np.mean([d.temp for d in similar_times]),
                'hum': np.mean([d.hum for d in similar_times]),
                'light': np.mean([d.light for d in similar_times]),
                'snd': np.mean([d.snd for d in similar_times])
            }
            
            # Remove the target from inputs
            input_data = {k: v for k, v in avg_input.items() if k != target}
            
            try:
                predicted_value = predict_value(node_id, loc, target, input_data)
                predictions.append({
                    'timestamp': current_date,
                    'value': predicted_value
                })
            except Exception as e:
                print(f"Error predicting for {current_date}: {str(e)}")
        
        current_date += datetime.timedelta(minutes=15)  # 15-minute intervals
    
    return predictions

# Load models when the module is imported
load_all_models()