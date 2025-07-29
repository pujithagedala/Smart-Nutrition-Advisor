import pandas as pd
from sklearn.metrics.pairwise import euclidean_distances
from datetime import date

# Load dataset
df = pd.read_csv('data/food_dataset.csv')

def calculate_bmr(gender, weight, height, age):
    if gender == 'male':
        return 10 * weight + 6.25 * height - 5 * age + 5
    elif gender == 'female':
        return 10 * weight + 6.25 * height - 5 * age - 161
    else:
        return 10 * weight + 6.25 * height - 5 * age

def calculate_age(birthdate_str):
    birthdate = date.fromisoformat(birthdate_str)
    today = date.today()
    return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

def recommend_food(calories, proteins, carbohydrates, fat, top_k=3):
    input_vector = [[calories, proteins, carbohydrates, fat]]
    food_vectors = df[['calories', 'proteins', 'carbohydrates', 'fat']].values
    distances = euclidean_distances(input_vector, food_vectors)[0]
    df['distance'] = distances
    top_matches = df.sort_values('distance').head(top_k)
    return top_matches[['food_name', 'calories', 'proteins', 'carbohydrates', 'fat']].to_dict(orient='records')

def recommend_food_for_user(user_profile, top_k=3):
    gender = user_profile['gender']
    weight = user_profile['weight_kg']
    height = user_profile['height_cm']
    age = calculate_age(user_profile['date_of_birth'])
    activity = user_profile['activity_level']
    goal = user_profile['dietary_goals']

    bmr = calculate_bmr(gender, weight, height, age)
    activity_factors = {
        'sedentary': 1.2,
        'lightly_active': 1.375,
        'moderately_active': 1.55,
        'very_active': 1.725,
        'extra_active': 1.9
    }
    tdee = bmr * activity_factors.get(activity, 1.2)

    if goal == 'weight_loss':
        tdee -= 500
    elif goal == 'weight_gain':
        tdee += 500

    target_calories = tdee
    target_protein = weight * 1.6  # 1.6g per kg
    target_fat = (0.25 * target_calories) / 9
    target_carbs = (target_calories - (target_protein * 4 + target_fat * 9)) / 4

    return recommend_food(target_calories, target_protein, target_carbs, target_fat, top_k)
