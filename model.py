from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

mysql = MySQL()

class User:
    @staticmethod
    def create(username, email, password, first_name=None, last_name=None):
        password_hash = generate_password_hash(password)
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO users (username, email, password_hash, first_name, last_name)
            VALUES (%s, %s, %s, %s, %s)
        """, (username, email, password_hash, first_name, last_name))
        mysql.connection.commit()
        return cur.lastrowid

    @staticmethod
    def get_by_email(email):
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        return cur.fetchone()

    @staticmethod
    def update_profile(user_id, data):
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE users SET
                email = %s,
                first_name = %s,
                last_name = %s,
                date_of_birth = %s,
                gender = %s,
                height_cm = %s,
                weight_kg = %s,
                activity_level = %s,
                dietary_goals = %s
            WHERE user_id = %s
        """, (
            data['email'],
            data.get('first_name'),
            data.get('last_name'),
            data.get('date_of_birth'),
            data.get('gender'),
            data.get('height_cm'),
            data.get('weight_kg'),
            data.get('activity_level'),
            data.get('dietary_goals'),
            user_id
        ))
        mysql.connection.commit()

class FoodItem:
    @staticmethod
    def get_all():
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM food_items ORDER BY name")
        return cur.fetchall()

    @staticmethod
    def search(query):
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM food_items WHERE name LIKE %s LIMIT 10", (f"%{query}%",))
        return cur.fetchall()

class FoodLog:
    @staticmethod
    def add_entry(user_id, food_id, servings, meal_type, log_date, log_time):
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO food_log (user_id, food_id, servings, meal_type, log_date, log_time)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, food_id, servings, meal_type, log_date, log_time))
        mysql.connection.commit()
        return cur.lastrowid

    @staticmethod
    def get_entries(user_id, date=None):
        cur = mysql.connection.cursor()
        if date:
            cur.execute("""
                SELECT fl.*, f.name, f.calories, f.protein_g, f.carbs_g, f.fat_g
                FROM food_log fl
                JOIN food_items f ON fl.food_id = f.food_id
                WHERE fl.user_id = %s AND fl.log_date = %s
                ORDER BY fl.log_date DESC, fl.log_time DESC
            """, (user_id, date))
        else:
            cur.execute("""
                SELECT fl.*, f.name, f.calories, f.protein_g, f.carbs_g, f.fat_g
                FROM food_log fl
                JOIN food_items f ON fl.food_id = f.food_id
                WHERE fl.user_id = %s
                ORDER BY fl.log_date DESC, fl.log_time DESC
                LIMIT 5
            """, (user_id,))
        return cur.fetchall()

    @staticmethod
    def get_nutrition_summary(user_id, date):
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT SUM(f.calories * fl.servings) as total_calories,
                   SUM(f.protein_g * fl.servings) as total_protein,
                   SUM(f.carbs_g * fl.servings) as total_carbs,
                   SUM(f.fat_g * fl.servings) as total_fat
            FROM food_log fl
            JOIN food_items f ON fl.food_id = f.food_id
            WHERE fl.user_id = %s AND fl.log_date = %s
        """, (user_id, date))
        return cur.fetchone()

class Recommendation:
    @staticmethod
    def get_for_user(user_id, limit=None):
        cur = mysql.connection.cursor()
        if limit:
            cur.execute("""
                SELECT * FROM recommendations
                WHERE user_id = %s
                ORDER BY generated_at DESC
                LIMIT %s
            """, (user_id, limit))
        else:
            cur.execute("""
                SELECT * FROM recommendations
                WHERE user_id = %s
                ORDER BY generated_at DESC
            """, (user_id,))
        return cur.fetchall()