import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import joblib
import os

def train_and_save_model():
    print("Loading Big Data...")
    # Load the 5,000 rows we just generated
    df1 = pd.read_csv('data/synthetic_expenses.csv')
    df2 = pd.read_csv('data/training_boost.csv')
    
    df = pd.concat([df1, df2], ignore_index=True)
    
    # We want the AI to look at the Description (X) and guess the Category (y)
    X = df['Description']
    y = df['Category']
    
    
    print("Training AI Model...")
    # Create an AI pipeline: Text to Numbers -> Naive Bayes Classifier
    model = make_pipeline(TfidfVectorizer(ngram_range=(1,2),
           lowercase=True,
           strip_accents="unicode"), MultinomialNB())
    
    # Train the brain!
    model.fit(X, y)
    
    # Calculate accuracy
    accuracy = model.score(X, y) * 100
    print(f"Training Complete! Model Accuracy: {accuracy:.2f}%")
    
    # Save the 'Brain' to a file so the app can load it instantly
    model_path = 'ml/saved_brain.pkl'
    joblib.dump(model, model_path)
    print(f"Model successfully saved to {model_path}")

if __name__ == "__main__":
    train_and_save_model()