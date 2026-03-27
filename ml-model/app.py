#!/usr/bin/env python3
"""
CampusWell Analytics - Flask API Server
RESTful API for student stress prediction
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import pandas as pd
import numpy as np
import joblib
import os
import logging
from datetime import datetime
import json

# Import our ML model
from train_model import StressPredictionModel

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize ML model
model = StressPredictionModel()

# Load pre-trained model
MODEL_PATH = 'ml-model/stress_model.pkl'
if os.path.exists(MODEL_PATH):
    model.load_model(MODEL_PATH)
    logger.info("✅ ML model loaded successfully")
else:
    logger.warning("⚠️  No pre-trained model found. Please run train_model.py first")

@app.route('/')
def index():
    """Serve the main application"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('.', filename)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'model_loaded': model.best_model is not None,
        'model_accuracy': model.best_score if model.best_model else None
    })

@app.route('/api/predict', methods=['POST'])
def predict_stress():
    """Predict stress level for student data"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No data provided',
                'message': 'Please provide student data in JSON format'
            }), 400
        
        # Validate required fields
        required_fields = [
            'age', 'gender', 'study_hours', 'attendance', 'exam_score',
            'sleep_hours', 'screen_time', 'physical_activity', 'caffeine_intake',
            'assignment_pressure', 'exam_fear', 'social_support', 'financial_pressure',
            'commute_time', 'extracurricular'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing_fields': missing_fields
            }), 400
        
        # Validate data ranges
        validation_errors = validate_input_data(data)
        if validation_errors:
            return jsonify({
                'error': 'Invalid data',
                'validation_errors': validation_errors
            }), 400
        
        # Make prediction
        if model.best_model is None:
            return jsonify({
                'error': 'Model not available',
                'message': 'ML model is not loaded. Please train the model first.'
            }), 503
        
        # Get prediction
        result = model.predict_stress(data)
        
        if result is None:
            return jsonify({
                'error': 'Prediction failed',
                'message': 'Unable to generate stress prediction'
            }), 500
        
        # Add metadata
        result['timestamp'] = datetime.now().isoformat()
        result['request_id'] = generate_request_id()
        
        # Log prediction for monitoring
        logger.info(f"Prediction made: {result['prediction']} (confidence: {result['confidence']:.1f}%)")
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/model/info', methods=['GET'])
def model_info():
    """Get information about the loaded model"""
    if model.best_model is None:
        return jsonify({
            'error': 'No model loaded',
            'message': 'Please train and load a model first'
        }), 404
    
    return jsonify({
        'model_name': model.best_model,
        'accuracy': float(model.best_score),
        'model_type': 'Student Stress Prediction',
        'version': '2.0',
        'features_count': 20,
        'training_date': '2024-03-27',  # This would come from the saved model
        'feature_importance': model.feature_importance,
        'supported_predictions': ['low', 'medium', 'high']
    })

@app.route('/api/retrain', methods=['POST'])
def retrain_model():
    """Retrain the model with new data"""
    try:
        # This would require new training data
        # For now, just trigger retraining with existing data
        from train_model import main as train_main
        
        logger.info("🔄 Model retraining started...")
        train_main()
        
        # Reload the new model
        model.load_model(MODEL_PATH)
        
        return jsonify({
            'success': True,
            'message': 'Model retrained successfully',
            'new_accuracy': float(model.best_score),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Retraining error: {str(e)}")
        return jsonify({
            'error': 'Retraining failed',
            'message': str(e)
        }), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get prediction statistics and analytics"""
    # This would typically come from a database
    # For demo, return mock statistics
    return jsonify({
        'total_predictions': 1250,
        'stress_distribution': {
            'low': 425,
            'medium': 680,
            'high': 145
        },
        'average_confidence': 82.5,
        'top_factors': {
            'sleep_hours': 78,
            'assignment_pressure': 65,
            'study_hours': 52,
            'exam_fear': 48,
            'financial_pressure': 35
        },
        'recent_predictions': [
            {
                'timestamp': '2024-03-27T10:30:00',
                'prediction': 'medium',
                'confidence': 85.2
            },
            {
                'timestamp': '2024-03-27T10:15:00',
                'prediction': 'low',
                'confidence': 91.7
            }
        ]
    })

@app.route('/api/export/data', methods=['GET'])
def export_data():
    """Export prediction data"""
    try:
        # Generate sample data for export
        sample_data = generate_sample_export_data()
        
        return jsonify({
            'success': True,
            'data': sample_data,
            'export_timestamp': datetime.now().isoformat(),
            'total_records': len(sample_data)
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Export failed',
            'message': str(e)
        }), 500

def validate_input_data(data):
    """Validate input data ranges and types"""
    errors = []
    
    # Age validation
    if not isinstance(data.get('age'), (int, float)) or data['age'] < 16 or data['age'] > 30:
        errors.append('Age must be between 16 and 30')
    
    # Study hours validation
    if not isinstance(data.get('study_hours'), (int, float)) or data['study_hours'] < 0 or data['study_hours'] > 16:
        errors.append('Study hours must be between 0 and 16')
    
    # Sleep hours validation
    if not isinstance(data.get('sleep_hours'), (int, float)) or data['sleep_hours'] < 0 or data['sleep_hours'] > 12:
        errors.append('Sleep hours must be between 0 and 12')
    
    # Rating scales validation
    rating_fields = ['assignment_pressure', 'exam_fear', 'social_support', 'financial_pressure', 'extracurricular']
    for field in rating_fields:
        if field in data and (not isinstance(data[field], (int, float)) or data[field] < 1 or data[field] > 5):
            errors.append(f'{field} must be between 1 and 5')
    
    return errors

def generate_request_id():
    """Generate unique request ID"""
    import uuid
    return str(uuid.uuid4())[:8]

def generate_sample_export_data():
    """Generate sample data for export"""
    return [
        {
            'id': 1,
            'timestamp': '2024-03-27T09:00:00',
            'age': 20,
            'gender': 'female',
            'study_hours': 8,
            'sleep_hours': 6,
            'prediction': 'medium',
            'confidence': 85.3,
            'risk_score': 52
        },
        {
            'id': 2,
            'timestamp': '2024-03-27T09:15:00',
            'age': 22,
            'gender': 'male',
            'study_hours': 5,
            'sleep_hours': 8,
            'prediction': 'low',
            'confidence': 92.1,
            'risk_score': 28
        }
    ]

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Create directories if they don't exist
    os.makedirs('ml-model', exist_ok=True)
    
    print("🚀 CampusWell Analytics API Server")
    print("=" * 40)
    print("📊 ML Model:", model.best_model or "Not loaded")
    print("🎯 Accuracy:", f"{model.best_score:.4f}" if model.best_score else "N/A")
    print("🌐 Server: http://localhost:5000")
    print("=" * 40)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
