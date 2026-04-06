from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_cors import CORS
from functools import wraps

from config import Config
from services.db import mongo
from routes.workout_routes import workout_bp
from routes.meal_routes import meal_bp
from routes.sleep_routes import sleep_bp
from routes.ai import ai_bp

# ------------------------
# CREATE FLASK APP
# ------------------------
app = Flask(__name__)

# Load config from config.py
app.config.from_object(Config)

# Set secret key for login session
app.secret_key = app.config.get("SECRET_KEY", "mysecret123")

# Enable CORS
CORS(app)

# Connect MongoDB
mongo.init_app(app)


# ------------------------
# LOGIN REQUIRED DECORATOR
# This checks if user is logged in
# ------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# ------------------------
# LOGIN PAGE
# Demo username: admin
# Demo password: 1234
# ------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Simple demo login
        if username == "admin" and password == "1234":
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid username or password"

    return render_template("login.html", error=error)


# ------------------------
# LOGOUT
# Clears login session
# ------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ------------------------
# HEALTH ENDPOINT
# Used for testing / CI / Docker
# ------------------------
@app.route("/api/health")
def health():
    return jsonify({"status": "success"})


# ------------------------
# DASHBOARD
# Protected page
# Shows workout, meal and sleep summary
# ------------------------
@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard():
    try:
        workouts = list(mongo.db.workouts.find({}, {"_id": 0}))
        meals = list(mongo.db.meals.find({}, {"_id": 0}))
        sleeps = list(mongo.db.sleeps.find({}, {"_id": 0}))
    except Exception:
        workouts = []
        meals = []
        sleeps = []

    avg_workout = round(
        sum(w.get("duration", 0) for w in workouts) / len(workouts), 2
    ) if workouts else 0

    avg_sleep = round(
        sum(s.get("duration", 0) for s in sleeps) / len(sleeps), 2
    ) if sleeps else 0

    return render_template(
        "dashboard.html",
        workouts=workouts,
        meals=meals,
        sleeps=sleeps,
        avg_workout=avg_workout,
        avg_sleep=avg_sleep
    )


# ------------------------
# ADD WORKOUT PAGE
# Protected page
# Saves workout data into MongoDB
# ------------------------
@app.route("/add-workout", methods=["GET", "POST"])
@login_required
def add_workout_page():
    if request.method == "POST":
        data = request.form

        workout = {
            "workout_type": data.get("workout_type"),
            "duration": int(data.get("duration")),
            "calories_burned": int(data.get("calories_burned", 0)),
            "date": data.get("date")
        }

        mongo.db.workouts.insert_one(workout)
        return redirect(url_for("dashboard"))

    return render_template("add_workout.html")


# ------------------------
# ADD MEAL PAGE
# Protected page
# Saves meal data into MongoDB
# ------------------------
@app.route("/add-meal", methods=["GET", "POST"])
@login_required
def add_meal_page():
    if request.method == "POST":
        data = request.form

        meal = {
            "meal_type": data.get("meal_type"),
            "calories": int(data.get("calories"))
        }

        mongo.db.meals.insert_one(meal)
        return redirect(url_for("dashboard"))

    return render_template("add_meal.html")


# ------------------------
# ADD SLEEP PAGE
# Protected page
# Saves sleep data into MongoDB
# ------------------------
@app.route("/add-sleep", methods=["GET", "POST"])
@login_required
def add_sleep_page():
    if request.method == "POST":
        data = request.form

        sleep = {
            "duration": float(data.get("duration")),
            "quality": data.get("quality")
        }

        mongo.db.sleeps.insert_one(sleep)
        return redirect(url_for("dashboard"))

    return render_template("add_sleep.html")


# ------------------------
# REGISTER API BLUEPRINTS
# ------------------------
app.register_blueprint(workout_bp)
app.register_blueprint(meal_bp)
app.register_blueprint(sleep_bp)
app.register_blueprint(ai_bp)


# ------------------------
# RUN APP
# ------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)