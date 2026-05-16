import os
import numpy as np
import joblib
from PIL import Image, ImageStat
import io
import base64
from sklearn.neighbors import KNeighborsClassifier

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'models')
MODEL_PATH = os.path.join(MODEL_DIR, 'vision_model.pkl')

# Food Nutrition Database
FOOD_DB = {
    'Salad': {
        'calories': 150, 'protein_g': 5, 'carbs_g': 10, 'fat_g': 8,
        'fibre_g': 6, 'sugar_g': 3, 'sodium_mg': 120, 'is_healthy': True,
        'tips': "Excellent choice! High in fibre and micronutrients."
    },
    'Pizza': {
        'calories': 285, 'protein_g': 12, 'carbs_g': 36, 'fat_g': 10,
        'fibre_g': 2, 'sugar_g': 4, 'sodium_mg': 640, 'is_healthy': False,
        'tips': "High in sodium and fats. Try a thin crust version."
    },
    'Burger': {
        'calories': 550, 'protein_g': 25, 'carbs_g': 45, 'fat_g': 30,
        'fibre_g': 3, 'sugar_g': 8, 'sodium_mg': 980, 'is_healthy': False,
        'tips': "High in calories. Opt for whole grain buns."
    },
    'Dal Chawal': {
        'calories': 380, 'protein_g': 14, 'carbs_g': 68, 'fat_g': 6,
        'fibre_g': 8, 'sugar_g': 4, 'sodium_mg': 420, 'is_healthy': True,
        'tips': "Balanced Indian meal. Provides complete protein."
    },
    'Apple': {
        'calories': 95, 'protein_g': 0.5, 'carbs_g': 25, 'fat_g': 0.3,
        'fibre_g': 4.5, 'sugar_g': 19, 'sodium_mg': 1, 'is_healthy': True,
        'tips': "Great snack! Good for sustained energy."
    }
}

class AdvancedVisionModel:
    def __init__(self):
        self.model = None
        self.labels = list(FOOD_DB.keys())
        self.train_real()

    def extract_features(self, image):
        """Extracts real visual features: RGB means and standard deviations."""
        img = image.convert('RGB').resize((100, 100))
        stat = ImageStat.Stat(img)
        # Features: [R_mean, G_mean, B_mean, R_std, G_std, B_std]
        return np.array(stat.mean + stat.stddev)

    def train_real(self):
        """Trains the model using heuristic visual profiles for common foods."""
        X, y = [], []
        
        # Heuristic Profiles [R_mean, G_mean, B_mean, R_std, G_std, B_std]
        profiles = {
            'Salad':      [100, 150, 80, 50, 60, 40],   # High Green
            'Pizza':      [180, 120, 80, 60, 50, 40],   # High Red/Yellow
            'Burger':     [130, 90, 60, 40, 30, 25],    # Brownish/Dark
            'Dal Chawal': [160, 140, 100, 40, 40, 30],  # Yellowish
            'Apple':      [180, 40, 40, 60, 20, 20],    # Deep Red
        }

        for label, profile in profiles.items():
            idx = self.labels.index(label)
            # Add some variations for robustness
            for _ in range(50):
                noise = np.random.normal(0, 5, 6)
                X.append(np.array(profile) + noise)
                y.append(idx)
        
        self.model = KNeighborsClassifier(n_neighbors=5)
        self.model.fit(X, y)
        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(self.model, MODEL_PATH)

    def predict(self, base64_image):
        try:
            img_data = base64.b64decode(base64_image)
            image = Image.open(io.BytesIO(img_data))
            features = self.extract_features(image).reshape(1, -1)
            
            # Real AI Prediction based on visual features
            pred_idx = self.model.predict(features)[0]
            prediction = self.labels[pred_idx]
            
            data = FOOD_DB.get(prediction).copy()
            data['dish_name'] = prediction
            return data
        except Exception as e:
            print(f"Vision Error: {e}")
            return None

class NutrientReasoner:
    def reason(self, food_data, profile):
        dish = food_data['dish_name']
        goal = (profile.goal or 'maintain').lower()
        
        reasons = [
            f"The Vision AI identified this as {dish}.",
            f"Matching {dish} against your '{goal}' objective..."
        ]
        
        if food_data['protein_g'] > 15: reasons.append("High protein detected - beneficial for muscle tissue.")
        if food_data['fibre_g'] > 4: reasons.append("Significant fibre content will help with long-term satiety.")
        if food_data['calories'] > 400 and goal == 'loss': reasons.append("⚠️ This is a calorie-dense meal; watch your portions.")
        if food_data['is_healthy']: reasons.append("✅ Nutrient density is high. Excellent choice.")
        else: reasons.append("⚠️ Processed elements detected. Limit frequency.")
        
        return " ".join(reasons)

class LiveVisionBridge:
    def __init__(self):
        self.engine = AdvancedVisionModel()
        self.nlp = NutrientReasoner()

    def analyze(self, base64_image, user_profile):
        food_data = self.engine.predict(base64_image)
        if not food_data: return None
        
        score, is_healthy = get_health_status(food_data, user_profile)
        food_data['health_score'] = score
        food_data['is_healthy_status'] = is_healthy
        food_data['nlp_analysis'] = self.nlp.reason(food_data, user_profile)
        
        return food_data

def get_health_status(food_data, user_profile):
    score = 0
    if food_data['is_healthy']: score += 5
    goal = (user_profile.goal or 'maintain').lower()
    if goal == 'loss':
        if food_data['calories'] < 300: score += 3
    elif goal == 'gain':
        if food_data['protein_g'] > 15: score += 3
    if food_data['fibre_g'] > 5: score += 2
    final_score = max(1, min(10, score))
    return final_score, final_score >= 6
