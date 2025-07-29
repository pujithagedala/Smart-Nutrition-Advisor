from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from decimal import Decimal
import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Naveen@22'
app.config['MYSQL_DB'] = 'nutrition_advisor'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid email or password')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')

        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                INSERT INTO users (username, email, password_hash, first_name, last_name)
                VALUES (%s, %s, %s, %s, %s)
            """, (username, email, password, first_name, last_name))
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('login'))
        except Exception as e:
            mysql.connection.rollback()
            cur.close()
            return render_template('register.html', error=str(e))

    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    cur = mysql.connection.cursor()

    today = datetime.date.today().isoformat()

    cur.execute("""
        SELECT SUM(f.calories * fl.servings) as total_calories,
               SUM(f.protein_g * fl.servings) as total_protein,
               SUM(f.carbs_g * fl.servings) as total_carbs,
               SUM(f.fat_g * fl.servings) as total_fat
        FROM food_log fl
        JOIN food_items f ON fl.food_id = f.food_id
        WHERE fl.user_id = %s AND fl.log_date = %s
    """, (user_id, today))

    nutrition_summary = cur.fetchone()

    cur.execute("""
        SELECT fl.*, f.name, f.calories, f.protein_g, f.carbs_g, f.fat_g
        FROM food_log fl
        JOIN food_items f ON fl.food_id = f.food_id
        WHERE fl.user_id = %s
        ORDER BY fl.log_date DESC, fl.log_time DESC
        LIMIT 5
    """, (user_id,))

    recent_entries = cur.fetchall()

    # Convert servings to Decimal to fix Decimal * float bug
    for entry in recent_entries:
        entry['servings'] = Decimal(entry['servings'])

    cur.execute("""
        SELECT * FROM recommendations
        WHERE user_id = %s
        ORDER BY generated_at DESC
        LIMIT 3
    """, (user_id,))
    recommendations = cur.fetchall()

    cur.close()

    return render_template('dashboard.html',
                           nutrition_summary=nutrition_summary,
                           recent_entries=recent_entries,
                           recommendations=recommendations)

@app.route('/food_log', methods=['GET', 'POST'])
@login_required
def food_log():
    user_id = session['user_id']
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        food_id = request.form['food_id']
        servings = request.form['servings']
        meal_type = request.form['meal_type']
        log_date = request.form.get('log_date', datetime.date.today().isoformat())
        log_time = request.form.get('log_time', datetime.datetime.now().time().isoformat())

        cur.execute("""
            INSERT INTO food_log (user_id, food_id, servings, meal_type, log_date, log_time)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, food_id, servings, meal_type, log_date, log_time))
        mysql.connection.commit()

        generate_recommendations(user_id)

        return redirect(url_for('food_log'))

    date_filter = request.args.get('date', datetime.date.today().isoformat())

    cur.execute("""
        SELECT fl.*, f.name, f.calories, f.protein_g, f.carbs_g, f.fat_g
        FROM food_log fl
        JOIN food_items f ON fl.food_id = f.food_id
        WHERE fl.user_id = %s AND fl.log_date = %s
        ORDER BY fl.log_time DESC
    """, (user_id, date_filter))

    log_entries = cur.fetchall()

    # ✅ Fix Decimal * float bug here
    for entry in log_entries:
        entry['servings'] = Decimal(entry['servings'])

    cur.execute("SELECT * FROM food_items ORDER BY name")
    food_items = cur.fetchall()
    cur.close()

    return render_template('food_log.html',
                           log_entries=log_entries,
                           food_items=food_items,
                           selected_date=date_filter,
                           datetime=datetime)

@app.route('/delete_food_log/<int:log_id>', methods=['POST'])
@login_required
def delete_food_log(log_id):
    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM food_log WHERE log_id = %s AND user_id = %s", (log_id, user_id))
    mysql.connection.commit()
    cur.close()

    generate_recommendations(user_id)

    return redirect(url_for('food_log'))

@app.route('/recommendations')
@login_required
def recommendations():
    user_id = session['user_id']

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT * FROM recommendations
        WHERE user_id = %s
        ORDER BY generated_at DESC
    """, (user_id,))
    recommendations = cur.fetchall()
    cur.close()

    return render_template('recommendations.html', recommendations=recommendations)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session['user_id']

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        date_of_birth = request.form.get('date_of_birth')
        gender = request.form.get('gender')
        height_cm = request.form.get('height_cm')
        weight_kg = request.form.get('weight_kg')
        activity_level = request.form.get('activity_level')
        dietary_goals = request.form.get('dietary_goals')

        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE users 
            SET first_name = %s, last_name = %s, date_of_birth = %s, 
                gender = %s, height_cm = %s, weight_kg = %s, 
                activity_level = %s, dietary_goals = %s
            WHERE user_id = %s
        """, (first_name, last_name, date_of_birth, gender, height_cm,
              weight_kg, activity_level, dietary_goals, user_id))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('profile'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()

    return render_template('profile.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Dummy placeholder for generate_recommendations (You should have your real logic here)
from ml_recommender import recommend_food

def generate_recommendations(user_id):
    cur = mysql.connection.cursor()
    today = datetime.date.today().isoformat()

    cur.execute("""
        SELECT 
            SUM(f.calories * fl.servings) AS total_calories,
            SUM(f.protein_g * fl.servings) AS total_protein,
            SUM(f.carbs_g * fl.servings) AS total_carbs,
            SUM(f.fat_g * fl.servings) AS total_fat
        FROM food_log fl
        JOIN food_items f ON fl.food_id = f.food_id
        WHERE fl.user_id = %s AND fl.log_date = %s
    """, (user_id, today))

    summary = cur.fetchone()

    if summary and summary['total_calories']:
        calories = summary['total_calories']
        protein = summary['total_protein']
        carbs = summary['total_carbs']
        fat = summary['total_fat']

        recommendations = recommend_food(calories, protein, carbs, fat, top_k=3)

        # Clear previous
        cur.execute("DELETE FROM recommendations WHERE user_id = %s", (user_id,))
        for rec in recommendations:
            rec_text = f"{rec['food_name']} "
            cur.execute("""
                INSERT INTO recommendations (user_id, recommendation_text, generated_at)
                VALUES (%s, %s, NOW())
            """, (user_id, rec_text))

        mysql.connection.commit()

    cur.close()


if __name__ == '__main__':
    app.run(debug=True)
