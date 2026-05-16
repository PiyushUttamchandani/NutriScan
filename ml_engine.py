import os
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import joblib

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'models')
CSV_PATH  = os.path.join(BASE_DIR, 'data', 'food.csv')

os.makedirs(MODEL_DIR, exist_ok=True)


def train_calorie_predictor():
    print("Training Calorie Predictor...")
    data = {
        'age':    [20,25,30,35,40,22,28,33,45,19,21,26,31,36,41,23,29,34,46,18],
        'weight': [60,70,80,90,75,55,65,85,95,50,58,72,82,88,77,53,67,83,91,48],
        'height': [165,170,175,180,172,160,168,178,182,158,163,171,176,179,173,162,169,177,181,157],
        'gender': [1,1,1,1,0,0,0,1,1,0,0,1,1,0,1,0,1,0,1,0],
        'goal':   [0,1,2,0,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1],
        'calories':[1800,2500,2200,1800,2000,1600,2200,2500,1800,1600,
                    1700,2500,2200,2000,2300,1650,2400,2100,1850,1550],
    }
    df    = pd.DataFrame(data)
    X     = df[['age','weight','height','gender','goal']]
    y     = df['calories']
    model = LinearRegression()
    model.fit(X, y)
    joblib.dump(model, os.path.join(MODEL_DIR, 'calorie_predictor.pkl'))
    print("  -> calorie_predictor.pkl saved!")


def train_workout_suggester():
    print("Training Workout Suggester...")

    # Logic:
    # BMI < 18.5  + any goal    → balanced
    # BMI 18.5-24.9 + loss      → cardio
    # BMI 18.5-24.9 + maintain  → balanced
    # BMI 18.5-24.9 + gain      → strength
    # BMI 25-29.9 + any goal    → cardio
    # BMI 30+     + any goal    → cardio

    rows = []

    # Underweight (BMI 13-18.4) — sabhi goals → balanced
    for bmi in [13, 14, 15, 16, 17, 17.5, 18, 18.3]:
        for goal in [0, 1, 2]:
            rows.append({'bmi': bmi, 'goal': goal, 'plan': 1})

    # Normal (BMI 18.5-24.9) + loss → cardio
    for bmi in [18.5, 19, 20, 21, 22, 23, 24, 24.5]:
        rows.append({'bmi': bmi, 'goal': 0, 'plan': 0})

    # Normal (BMI 18.5-24.9) + maintain → balanced
    for bmi in [18.5, 19, 20, 21, 22, 23, 24, 24.5]:
        rows.append({'bmi': bmi, 'goal': 2, 'plan': 1})

    # Normal (BMI 18.5-24.9) + gain → strength
    for bmi in [18.5, 19, 20, 21, 22, 23, 24, 24.5]:
        rows.append({'bmi': bmi, 'goal': 1, 'plan': 2})

    # Overweight (BMI 25-29.9) — sabhi goals → cardio
    for bmi in [25, 26, 27, 27.5, 28, 29, 29.5]:
        for goal in [0, 1, 2]:
            rows.append({'bmi': bmi, 'goal': goal, 'plan': 0})

    # Obese (BMI 30+) — sabhi goals → cardio
    for bmi in [30, 31, 32, 33, 34, 35, 38, 40]:
        for goal in [0, 1, 2]:
            rows.append({'bmi': bmi, 'goal': goal, 'plan': 0})

    df  = pd.DataFrame(rows)
    knn = KNeighborsClassifier(n_neighbors=5)
    knn.fit(df[['bmi', 'goal']], df['plan'])
    joblib.dump(knn, os.path.join(MODEL_DIR, 'workout_knn.pkl'))
    print("  -> workout_knn.pkl saved!")


def train_meal_recommender():
    print("Training Meal Recommender...")

    if os.path.exists(CSV_PATH):
        print("  food.csv mila!")
        df = pd.read_csv(CSV_PATH)
        df.columns = df.columns.str.strip().str.lower()

        for col in ['name', 'ingredients', 'course']:
            if col not in df.columns:
                df[col] = ''

        df.dropna(subset=['name'], inplace=True)
        df.fillna('', inplace=True)

        if 'prep_time' in df.columns:
            df['prep_time'] = pd.to_numeric(df['prep_time'], errors='coerce').fillna(30)
        else:
            df['prep_time'] = 30

    else:
        print("  food.csv nahi mila! Dummy data use ho raha hai.")
        df = pd.DataFrame({
            'name':        ['Dal Tadka','Paneer Butter Masala','Aloo Paratha','Grilled Chicken',
                            'Oats Upma','Fruit Salad','Rajma Chawal','Egg Bhurji','Vegetable Biryani'],
            'ingredients': ['dal lentil onion tomato','paneer cream butter tomato','potato wheat ghee',
                            'chicken olive oil herbs','oats vegetables','apple banana mango',
                            'kidney beans rice','eggs onion tomato','rice vegetables spices'],
            'course':      ['main course','main course','breakfast','main course',
                            'breakfast','dessert','main course','breakfast','main course'],
            'prep_time':   [20, 30, 25, 15, 10, 5, 40, 10, 45],
        })

    df['combined'] = df['name'] + ' ' + df['ingredients'] + ' ' + df['course']
    tfidf          = TfidfVectorizer(stop_words='english')
    tfidf_matrix   = tfidf.fit_transform(df['combined'])
    similarity     = cosine_similarity(tfidf_matrix, tfidf_matrix)
    df             = df.reset_index(drop=True)

    joblib.dump(tfidf,      os.path.join(MODEL_DIR, 'tfidf_vectorizer.pkl'))
    joblib.dump(similarity, os.path.join(MODEL_DIR, 'meal_similarity.pkl'))
    joblib.dump(df,         os.path.join(MODEL_DIR, 'food_df.pkl'))
    print("  -> meal models saved!")


if __name__ == '__main__':
    train_calorie_predictor()
    train_workout_suggester()
    train_meal_recommender()
    
    # Train Vision Model V4 (from Image Database)
    try:
        from vision_v4 import bridge
        bridge.vision.train_from_db()
        print("Vision Model V4 (DB Trained) saved!")
    except Exception as e:
        print(f"Vision model V4 training failed: {e}")
        
    # print("\nSabhi models ban gaye! Ab manage.py run karo.")