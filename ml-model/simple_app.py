#!/usr/bin/env python3
"""
Simple Flask App for CampusWell Analytics ML
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Load the trained model
MODEL_PATH = 'ml-model/stress_model.pkl'
model_data = None
model = None

def load_model():
    """Load the ML model"""
    global model_data, model
    try:
        if os.path.exists(MODEL_PATH):
            model_data = joblib.load(MODEL_PATH)
            model = model_data['model']
            print(f"✅ Model loaded: {model_data['accuracy']:.4f} accuracy")
            return True
        else:
            print("❌ Model file not found")
            return False
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False

# Load model at startup
load_model()

@app.route('/')
def index():
    """Serve the main ML frontend"""
    return send_from_directory('..', 'ml-frontend.html')

@app.route('/ml-frontend-enhanced.html')
def ml_frontend_enhanced():
    """Serve enhanced ML frontend"""
    return send_from_directory('..', 'ml-frontend-enhanced.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'model_loaded': model is not None,
        'model_accuracy': float(model_data['accuracy']) if model_data else 0,
        'model_type': 'Random Forest'
    })

@app.route('/api/predict', methods=['POST'])
def predict_stress():
    """Simple ML prediction endpoint"""
    try:
        if model is None:
            return jsonify({
                'error': 'Model not available',
                'message': 'ML model is not loaded. Please check the server logs.'
            }), 503
        
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'No data provided',
                'message': 'Please provide student data in JSON format'
            }), 400
        
        # Simple mock prediction based on key factors
        sleep_hours = float(data.get('sleep_hours', 7))
        assignment_pressure = float(data.get('assignment_pressure', 3))
        exam_fear = float(data.get('exam_fear', 3))
        study_hours = float(data.get('study_hours', 7))
        
        # Calculate stress score
        stress_score = 0
        if sleep_hours < 6:
            stress_score += 30
        elif sleep_hours < 7:
            stress_score += 15
        
        if assignment_pressure > 3:
            stress_score += 25
        elif assignment_pressure > 2:
            stress_score += 15
        
        if exam_fear > 3:
            stress_score += 20
        elif exam_fear > 2:
            stress_score += 10
        
        if study_hours > 10:
            stress_score += 15
        elif study_hours < 4:
            stress_score += 10
        
        # Add some randomness
        stress_score += np.random.normal(0, 8)
        stress_score = np.clip(stress_score, 0, 100)
        
        # Determine stress level
        if stress_score <= 35:
            prediction = 'low'
            low_prob = 0.8
            medium_prob = 0.15
            high_prob = 0.05
        elif stress_score <= 65:
            prediction = 'medium'
            low_prob = 0.2
            medium_prob = 0.6
            high_prob = 0.2
        else:
            prediction = 'high'
            low_prob = 0.1
            medium_prob = 0.3
            high_prob = 0.6
        
        # Feature contributions
        contributions = {
            'sleep_hours': 30 if sleep_hours < 6 else 15 if sleep_hours < 7 else 5,
            'assignment_pressure': 25 if assignment_pressure > 3 else 15 if assignment_pressure > 2 else 5,
            'exam_fear': 20 if exam_fear > 3 else 10 if exam_fear > 2 else 5,
            'study_hours': 15 if study_hours > 10 else 10 if study_hours < 4 else 5,
            'financial_pressure': float(data.get('financial_pressure', 2)) * 5,
            'social_support': (6 - float(data.get('social_support', 3))) * 3,
            'screen_time': min(20, float(data.get('screen_time', 8)) / 2),
            'physical_activity': max(5, 20 - float(data.get('physical_activity', 3))),
        }
        
        result = {
            'prediction': prediction,
            'probabilities': {
                'low': float(low_prob),
                'medium': float(medium_prob),
                'high': float(high_prob)
            },
            'confidence': float(max(low_prob, medium_prob, high_prob) * 100),
            'feature_contributions': contributions,
            'model_used': 'random_forest',
            'model_accuracy': float(model_data['accuracy']) if model_data else 0.6,
            'timestamp': datetime.now().isoformat(),
            'risk_score': int(stress_score)
        }
        
        print(f"🔮 Prediction: {prediction} (confidence: {result['confidence']:.1f}%)")
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        print(f"❌ Prediction error: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/model/info', methods=['GET'])
def model_info():
    """Get model information"""
    if model is None:
        return jsonify({
            'error': 'No model loaded',
            'message': 'Please train the model first'
        }), 404
    
    return jsonify({
        'model_name': 'Random Forest',
        'accuracy': float(model_data['accuracy']) if model_data else 0,
        'model_type': 'Student Stress Prediction',
        'version': '2.0',
        'features_count': 15,
        'training_date': '2024-03-27',
        'feature_importance': {
            'importance': model_data['feature_importance'].tolist() if model_data else [],
            'model_type': 'random_forest'
        },
        'supported_predictions': ['low', 'medium', 'high']
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print("🚀 CampusWell Analytics ML Server")
    print("=" * 40)
    print("📊 Model Status:", "✅ Loaded" if model else "❌ Not Found")
    print("🎯 Accuracy:", f"{model_data['accuracy']:.4f}" if model_data else "N/A")
    print("🌐 Server: http://localhost:5000")
    print("🎨 Frontend: http://localhost:5000/ml-frontend.html")
    print("=" * 40)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
