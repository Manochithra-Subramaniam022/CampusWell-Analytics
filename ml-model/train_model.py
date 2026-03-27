#!/usr/bin/env python3
"""
CampusWell Analytics - ML Model Training Pipeline
Advanced student stress prediction using machine learning
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.neural_network import MLPClassifier
import xgboost as xgb
import joblib
import warnings
warnings.filterwarnings('ignore')

class StressPredictionModel:
    """
    Advanced ML model for student stress prediction
    """
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.feature_importance = {}
        self.best_model = None
        self.best_score = 0
        
    def load_data(self, file_path='data/student_stress_data.csv'):
        """Load and preprocess student stress data"""
        try:
            # Generate synthetic dataset if file doesn't exist
            self.generate_synthetic_data(file_path)
            
            df = pd.read_csv(file_path)
            print(f"✅ Data loaded successfully: {df.shape}")
            return df
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return None
    
    def generate_synthetic_data(self, file_path, n_samples=1000):
        """Generate realistic synthetic student stress data"""
        np.random.seed(42)
        
        data = {
            # Personal factors
            'age': np.random.normal(20, 2, n_samples).clip(16, 30),
            'gender': np.random.choice(['male', 'female', 'other'], n_samples, p=[0.45, 0.5, 0.05]),
            
            # Academic factors
            'study_hours': np.random.gamma(2, 2, n_samples).clip(0, 16),
            'attendance': np.random.beta(8, 2, n_samples) * 100,
            'exam_score': np.random.normal(75, 15, n_samples).clip(0, 100),
            'assignment_pressure': np.random.choice([1, 2, 3, 4, 5], n_samples, p=[0.1, 0.2, 0.4, 0.2, 0.1]),
            
            # Lifestyle factors
            'sleep_hours': np.random.normal(7, 1.5, n_samples).clip(3, 12),
            'screen_time': np.random.gamma(2, 3, n_samples).clip(1, 16),
            'physical_activity': np.random.exponential(3, n_samples).clip(0, 20),
            'caffeine_intake': np.random.poisson(2, n_samples).clip(0, 10),
            
            # Psychological factors
            'exam_fear': np.random.choice([1, 2, 3, 4, 5], n_samples, p=[0.15, 0.25, 0.35, 0.15, 0.1]),
            'social_support': np.random.choice([1, 2, 3, 4, 5], n_samples, p=[0.1, 0.15, 0.3, 0.3, 0.15]),
            'financial_pressure': np.random.choice([1, 2, 3, 4, 5], n_samples, p=[0.2, 0.3, 0.3, 0.15, 0.05]),
            
            # Environmental factors
            'commute_time': np.random.exponential(1, n_samples).clip(0, 4),
            'extracurricular': np.random.choice([1, 2, 3, 4, 5], n_samples, p=[0.2, 0.25, 0.3, 0.15, 0.1])
        }
        
        df = pd.DataFrame(data)
        
        # Generate stress labels based on weighted formula
        stress_scores = (
            df['study_hours'].apply(lambda x: 15 if x > 10 else 10 if x < 4 else 5) +
            df['sleep_hours'].apply(lambda x: 25 if x < 5 else 15 if x < 7 else 5) +
            df['assignment_pressure'] * 8 +
            df['exam_fear'] * 7 +
            df['financial_pressure'] * 5 +
            df['screen_time'].apply(lambda x: 10 if x > 12 else 5 if x > 8 else 2) +
            np.random.normal(0, 5, n_samples)  # Add noise
        )
        
        # Categorize stress levels
        df['stress_level'] = pd.cut(stress_scores, 
                                   bins=[-np.inf, 35, 70, np.inf], 
                                   labels=['low', 'medium', 'high'])
        
        # Add some realistic correlations
        df.loc[df['sleep_hours'] < 6, 'exam_score'] -= 10
        df.loc[df['study_hours'] > 12, 'sleep_hours'] -= 1
        df.loc[df['social_support'] < 2, 'exam_fear'] += 1
        
        df['exam_score'] = df['exam_score'].clip(0, 100)
        df.to_csv(file_path, index=False)
        print(f"✅ Synthetic data generated: {file_path}")
        
    def preprocess_data(self, df):
        """Preprocess and engineer features"""
        print("🔄 Preprocessing data...")
        
        # Handle missing values
        df = df.dropna()
        
        # Encode categorical variables
        categorical_cols = ['gender']
        for col in categorical_cols:
            if col not in self.encoders:
                self.encoders[col] = LabelEncoder()
                df[col + '_encoded'] = self.encoders[col].fit_transform(df[col])
            else:
                df[col + '_encoded'] = self.encoders[col].transform(df[col])
        
        # Feature engineering
        df['study_sleep_ratio'] = df['study_hours'] / df['sleep_hours']
        df['screen_study_ratio'] = df['screen_time'] / df['study_hours']
        df['academic_load'] = df['assignment_pressure'] * df['study_hours']
        df['lifestyle_balance'] = df['physical_activity'] / (df['screen_time'] + 1)
        df['support_pressure_ratio'] = df['social_support'] / (df['financial_pressure'] + 1)
        
        # Select features for modeling
        feature_cols = [
            'age', 'gender_encoded', 'study_hours', 'attendance', 'exam_score',
            'assignment_pressure', 'sleep_hours', 'screen_time', 'physical_activity',
            'caffeine_intake', 'exam_fear', 'social_support', 'financial_pressure',
            'commute_time', 'extracurricular', 'study_sleep_ratio', 
            'screen_study_ratio', 'academic_load', 'lifestyle_balance', 'support_pressure_ratio'
        ]
        
        X = df[feature_cols]
        y = df['stress_level']
        
        # Scale features
        if 'scaler' not in self.scalers:
            self.scalers['scaler'] = StandardScaler()
            X_scaled = self.scalers['scaler'].fit_transform(X)
        else:
            X_scaled = self.scalers['scaler'].transform(X)
        
        return X_scaled, y, feature_cols
    
    def train_models(self, X, y):
        """Train multiple ML models and select the best"""
        print("🚀 Training ML models...")
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Model configurations
        models_config = {
            'random_forest': {
                'model': RandomForestClassifier(random_state=42),
                'params': {
                    'n_estimators': [100, 200, 300],
                    'max_depth': [10, 15, 20, None],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4]
                }
            },
            'gradient_boosting': {
                'model': GradientBoostingClassifier(random_state=42),
                'params': {
                    'n_estimators': [100, 200],
                    'learning_rate': [0.01, 0.1, 0.2],
                    'max_depth': [3, 5, 7]
                }
            },
            'xgboost': {
                'model': xgb.XGBClassifier(random_state=42),
                'params': {
                    'n_estimators': [100, 200],
                    'learning_rate': [0.01, 0.1, 0.2],
                    'max_depth': [3, 5, 7],
                    'subsample': [0.8, 0.9, 1.0]
                }
            },
            'neural_network': {
                'model': MLPClassifier(random_state=42, max_iter=1000),
                'params': {
                    'hidden_layer_sizes': [(50,), (100,), (50, 25)],
                    'alpha': [0.0001, 0.001, 0.01],
                    'learning_rate_init': ['constant', 'adaptive']
                }
            }
        }
        
        # Train and evaluate each model
        for name, config in models_config.items():
            print(f"\n📊 Training {name.replace('_', ' ').title()}...")
            
            # Grid search for hyperparameter tuning
            grid_search = GridSearchCV(
                config['model'], 
                config['params'], 
                cv=5, 
                scoring='accuracy',
                n_jobs=-1
            )
            
            grid_search.fit(X_train, y_train)
            best_model = grid_search.best_estimator_
            
            # Evaluate model
            y_pred = best_model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Cross-validation
            cv_scores = cross_val_score(best_model, X_train, y_train, cv=5, scoring='accuracy')
            
            self.models[name] = best_model
            
            print(f"   ✅ Best params: {grid_search.best_params_}")
            print(f"   📈 Test Accuracy: {accuracy:.4f}")
            print(f"   🔄 CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
            
            # Track best model
            if accuracy > self.best_score:
                self.best_score = accuracy
                self.best_model = name
                self.feature_importance = self.get_feature_importance(best_model, name)
            
            # Detailed classification report
            print(f"   📋 Classification Report:")
            print(classification_report(y_test, y_pred))
        
        print(f"\n🏆 Best Model: {self.best_model.replace('_', ' ').title()} (Accuracy: {self.best_score:.4f})")
        
    def get_feature_importance(self, model, model_name):
        """Extract feature importance from trained model"""
        if hasattr(model, 'feature_importances_'):
            return {
                'importance': model.feature_importances_,
                'model_type': model_name
            }
        return None
    
    def evaluate_model(self, X_test, y_test):
        """Comprehensive model evaluation"""
        if not self.best_model:
            print("❌ No trained model found!")
            return
        
        model = self.models[self.best_model]
        y_pred = model.predict(X_test)
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        # Visualization
        plt.figure(figsize=(15, 5))
        
        # Confusion Matrix
        plt.subplot(1, 3, 1)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=['Low', 'Medium', 'High'], 
                   yticklabels=['Low', 'Medium', 'High'])
        plt.title('Confusion Matrix')
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        
        # Feature Importance
        if self.feature_importance:
            plt.subplot(1, 3, 2)
            importance = self.feature_importance['importance']
            feature_names = [f'F{i+1}' for i in range(len(importance))]
            indices = np.argsort(importance)[::-1][:10]  # Top 10 features
            
            plt.bar(range(10), importance[indices])
            plt.title('Top 10 Feature Importance')
            plt.xlabel('Features')
            plt.ylabel('Importance')
            plt.xticks(range(10), [f'F{i+1}' for i in indices], rotation=45)
        
        # Model Comparison
        plt.subplot(1, 3, 3)
        model_names = list(self.models.keys())
        accuracies = []
        for name in model_names:
            acc = accuracy_score(y_test, self.models[name].predict(X_test))
            accuracies.append(acc)
        
        plt.bar(model_names, accuracies)
        plt.title('Model Comparison')
        plt.xlabel('Models')
        plt.ylabel('Accuracy')
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig('ml-model/model_evaluation.png', dpi=300, bbox_inches='tight')
        plt.show()
        
    def save_model(self, model_path='ml-model/stress_model.pkl'):
        """Save the trained model and preprocessing objects"""
        if not self.best_model:
            print("❌ No model to save!")
            return
        
        model_data = {
            'model': self.models[self.best_model],
            'scaler': self.scalers['scaler'],
            'encoders': self.encoders,
            'feature_importance': self.feature_importance,
            'best_model_name': self.best_model,
            'accuracy': self.best_score,
            'metadata': {
                'model_type': 'Student Stress Prediction',
                'version': '2.0',
                'training_date': pd.Timestamp.now().isoformat(),
                'features': 20  # Updated count with engineered features
            }
        }
        
        joblib.dump(model_data, model_path)
        print(f"✅ Model saved to {model_path}")
        print(f"📊 Model: {self.best_model}")
        print(f"🎯 Accuracy: {self.best_score:.4f}")
        
    def load_model(self, model_path='ml-model/stress_model.pkl'):
        """Load pre-trained model"""
        try:
            model_data = joblib.load(model_path)
            self.models = {'loaded': model_data['model']}
            self.scalers = {'scaler': model_data['scaler']}
            self.encoders = model_data['encoders']
            self.feature_importance = model_data['feature_importance']
            self.best_model = model_data['best_model_name']
            self.best_score = model_data['accuracy']
            print(f"✅ Model loaded from {model_path}")
            return True
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def predict_stress(self, student_data):
        """Make stress prediction for new student data"""
        if not self.best_model:
            print("❌ No trained model available!")
            return None
        
        try:
            # Convert to DataFrame if needed
            if isinstance(student_data, dict):
                df = pd.DataFrame([student_data])
            else:
                df = student_data.copy()
            
            # Apply same preprocessing
            for col in ['gender']:
                if col in self.encoders:
                    df[col + '_encoded'] = self.encoders[col].transform(df[col])
            
            # Feature engineering
            df['study_sleep_ratio'] = df['study_hours'] / df['sleep_hours']
            df['screen_study_ratio'] = df['screen_time'] / df['study_hours']
            df['academic_load'] = df['assignment_pressure'] * df['study_hours']
            df['lifestyle_balance'] = df['physical_activity'] / (df['screen_time'] + 1)
            df['support_pressure_ratio'] = df['social_support'] / (df['financial_pressure'] + 1)
            
            # Select features in correct order
            feature_cols = [
                'age', 'gender_encoded', 'study_hours', 'attendance', 'exam_score',
                'assignment_pressure', 'sleep_hours', 'screen_time', 'physical_activity',
                'caffeine_intake', 'exam_fear', 'social_support', 'financial_pressure',
                'commute_time', 'extracurricular', 'study_sleep_ratio', 
                'screen_study_ratio', 'academic_load', 'lifestyle_balance', 'support_pressure_ratio'
            ]
            
            X = df[feature_cols]
            X_scaled = self.scalers['scaler'].transform(X)
            
            # Make prediction
            model = self.models[self.best_model]
            prediction = model.predict(X_scaled)[0]
            probabilities = model.predict_proba(X_scaled)[0]
            
            # Get feature contributions
            contributions = self.get_feature_contributions(X_scaled[0])
            
            result = {
                'prediction': prediction,
                'probabilities': {
                    'low': float(probabilities[0]),
                    'medium': float(probabilities[1]),
                    'high': float(probabilities[2])
                },
                'confidence': float(np.max(probabilities) * 100),
                'feature_contributions': contributions,
                'model_used': self.best_model,
                'model_accuracy': float(self.best_score)
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            return None
    
    def get_feature_contributions(self, features):
        """Calculate individual feature contributions to prediction"""
        if not self.feature_importance:
            return {}
        
        importance = self.feature_importance['importance']
        contributions = {}
        
        feature_names = [
            'age', 'gender', 'study_hours', 'attendance', 'exam_score',
            'assignment_pressure', 'sleep_hours', 'screen_time', 'physical_activity',
            'caffeine_intake', 'exam_fear', 'social_support', 'financial_pressure',
            'commute_time', 'extracurricular', 'study_sleep_ratio', 
            'screen_study_ratio', 'academic_load', 'lifestyle_balance', 'support_pressure_ratio'
        ]
        
        for i, feature in enumerate(feature_names):
            if i < len(importance):
                contributions[feature] = float(importance[i] * 100)
        
        return contributions

def main():
    """Main training pipeline"""
    print("🚀 CampusWell Analytics - ML Model Training")
    print("=" * 50)
    
    # Initialize model
    model = StressPredictionModel()
    
    # Load data
    df = model.load_data()
    if df is None:
        return
    
    # Preprocess
    X, y, feature_names = model.preprocess_data(df)
    
    # Train models
    model.train_models(X, y)
    
    # Split for final evaluation
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Evaluate
    model.evaluate_model(X_test, y_test)
    
    # Save model
    model.save_model()
    
    print("\n🎉 Training completed successfully!")
    print("=" * 50)

if __name__ == "__main__":
    main()
