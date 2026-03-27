#!/usr/bin/env python3
"""
Simple ML Model Training for CampusWell Analytics
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib
import os

def generate_simple_data(n_samples=500):
    """Generate simple synthetic data"""
    np.random.seed(42)
    
    data = {
        'age': np.random.normal(20, 2, n_samples).clip(16, 30),
        'gender': np.random.choice(['male', 'female'], n_samples),
        'study_hours': np.random.gamma(2, 2, n_samples).clip(0, 16),
        'attendance': np.random.beta(8, 2, n_samples) * 100,
        'exam_score': np.random.normal(75, 15, n_samples).clip(0, 100),
        'assignment_pressure': np.random.choice([1, 2, 3, 4, 5], n_samples, p=[0.1, 0.2, 0.4, 0.2, 0.1]),
        'sleep_hours': np.random.normal(7, 1.5, n_samples).clip(3, 12),
        'screen_time': np.random.gamma(2, 3, n_samples).clip(1, 16),
        'physical_activity': np.random.exponential(3, n_samples).clip(0, 20),
        'caffeine_intake': np.random.poisson(2, n_samples).clip(0, 10),
        'exam_fear': np.random.choice([1, 2, 3, 4, 5], n_samples, p=[0.15, 0.25, 0.35, 0.15, 0.1]),
        'social_support': np.random.choice([1, 2, 3, 4, 5], n_samples, p=[0.1, 0.15, 0.3, 0.3, 0.15]),
        'financial_pressure': np.random.choice([1, 2, 3, 4, 5], n_samples, p=[0.2, 0.3, 0.3, 0.15, 0.05]),
        'commute_time': np.random.exponential(1, n_samples).clip(0, 4),
        'extracurricular': np.random.choice([1, 2, 3, 4, 5], n_samples, p=[0.2, 0.25, 0.3, 0.15, 0.1])
    }
    
    df = pd.DataFrame(data)
    
    # Generate stress scores with better distribution
    np.random.seed(123)
    stress_scores = (
        df['study_hours'].apply(lambda x: 15 if x > 10 else 10 if x < 4 else 5) +
        df['sleep_hours'].apply(lambda x: 25 if x < 5 else 15 if x < 7 else 5) +
        df['assignment_pressure'] * 8 +
        df['exam_fear'] * 7 +
        df['financial_pressure'] * 5 +
        df['screen_time'].apply(lambda x: 10 if x > 12 else 5 if x > 8 else 2) +
        np.random.normal(0, 5, n_samples)
    )
    
    # Create balanced stress levels
    stress_scores = np.clip(stress_scores, 0, 100)
    
    # Create more balanced distribution
    low_threshold = np.percentile(stress_scores, 33)
    high_threshold = np.percentile(stress_scores, 67)
    
    df['stress_level'] = pd.cut(stress_scores, 
                                   bins=[-np.inf, low_threshold, high_threshold, np.inf], 
                                   labels=['low', 'medium', 'high'])
    
    # Ensure all classes have enough samples
    min_samples_per_class = max(10, n_samples // 20)
    
    # Balance the dataset
    balanced_data = []
    for level in ['low', 'medium', 'high']:
        class_data = df[df['stress_level'] == level]
        if len(class_data) < min_samples_per_class:
            # Oversample if needed
            class_data = class_data.sample(min_samples_per_class, replace=True, random_state=42)
        else:
            class_data = class_data.sample(min_samples_per_class, random_state=42)
        balanced_data.append(class_data)
    
    df_balanced = pd.concat(balanced_data, ignore_index=True)
    
    # Save data
    os.makedirs('data', exist_ok=True)
    df_balanced.to_csv('data/student_stress_data.csv', index=False)
    
    print(f"✅ Generated balanced dataset: {df_balanced.shape}")
    print(f"📊 Stress distribution: {df_balanced['stress_level'].value_counts().to_dict()}")
    
    return df_balanced

def train_simple_model():
    """Train a simple Random Forest model"""
    print("🚀 Training ML Model...")
    
    # Generate data
    df = generate_simple_data()
    
    # Prepare features
    feature_cols = [
        'age', 'study_hours', 'attendance', 'exam_score',
        'assignment_pressure', 'sleep_hours', 'screen_time', 'physical_activity',
        'caffeine_intake', 'exam_fear', 'social_support', 'financial_pressure',
        'commute_time', 'extracurricular'
    ]
    
    # Encode gender
    le = LabelEncoder()
    df['gender_encoded'] = le.fit_transform(df['gender'])
    feature_cols = ['gender_encoded'] + [col for col in feature_cols if col != 'gender']
    
    X = df[feature_cols]
    y = df['stress_level']
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Train model
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        min_samples_split=5,
        min_samples_leaf=2
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    
    print(f"📈 Training Accuracy: {train_score:.4f}")
    print(f"📊 Test Accuracy: {test_score:.4f}")
    
    # Feature importance
    feature_importance = model.feature_importances_
    feature_names = feature_cols
    
    # Save model
    os.makedirs('ml-model', exist_ok=True)
    
    model_data = {
        'model': model,
        'scaler': scaler,
        'encoder': le,
        'feature_names': feature_names,
        'feature_importance': feature_importance,
        'accuracy': float(test_score),
        'metadata': {
            'model_type': 'Student Stress Prediction',
            'version': '2.0',
            'training_date': pd.Timestamp.now().isoformat(),
            'features': len(feature_names)
        }
    }
    
    joblib.dump(model_data, 'ml-model/stress_model.pkl')
    print(f"✅ Model saved to ml-model/stress_model.pkl")
    print(f"🎯 Final Accuracy: {test_score:.4f}")
    
    return model_data

if __name__ == "__main__":
    train_simple_model()
