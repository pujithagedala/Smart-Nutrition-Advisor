CREATE DATABASE nutrition_advisor;

USE nutrition_advisor;

-- Users table
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    date_of_birth DATE,
    gender ENUM('male', 'female', 'other'),
    height_cm INT,
    weight_kg DECIMAL(5,2),
    activity_level ENUM('sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extra_active'),
    dietary_goals ENUM('weight_loss', 'weight_gain', 'maintenance', 'muscle_gain'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Food items table
CREATE TABLE food_items (
    food_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    calories INT NOT NULL,
    protein_g DECIMAL(5,2),
    carbs_g DECIMAL(5,2),
    fat_g DECIMAL(5,2),
    fiber_g DECIMAL(5,2),
    sugar_g DECIMAL(5,2),
    sodium_mg DECIMAL(5,2),
    serving_size VARCHAR(50),
    category VARCHAR(50)
);

-- User food log
CREATE TABLE food_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    food_id INT NOT NULL,
    servings DECIMAL(3,2) NOT NULL,
    meal_type ENUM('breakfast', 'lunch', 'dinner', 'snack'),
    log_date DATE NOT NULL,
    log_time TIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (food_id) REFERENCES food_items(food_id)
);

-- Nutrition recommendations
CREATE TABLE recommendations (
    recommendation_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    recommendation_text TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);