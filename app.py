from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_cors import CORS
from config import Config
from services.db import mongo
from routes.workout_routes import workout_bp

# Initialize app
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
mongo.init_app(app)

# ------------------------
# DASHBOARD
# ------------------------
@app.route("/")
@app.route("/dashboard")
def dashboard():
    # Fetch data from MongoDB
    workouts = list(mongo.db.workouts.find({}, {"_id": 0}))
    meals = list(mongo.db.meals.find({}, {"_id": 0}))
    sleeps = list(mongo.db.sleeps.find({}, {"_id": 0}))

    # Calculate averages
    avg_workout = round(sum(w['duration'] for w in workouts)/len(workouts), 2) if workouts else 0
    avg_sleep = round(sum(s['duration'] for s in sleeps)/len(sleeps), 2) if sleeps else 0

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
# ------------------------
@app.route("/add-workout", methods=["GET", "POST"])
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
# ------------------------
@app.route("/add-meal", methods=["GET", "POST"])
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
# ------------------------
@app.route("/add-sleep", methods=["GET", "POST"])
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
# ADD AI INSIGHTS
# ------------------------
@app.route("/ai-insights", methods=["GET", "POST"])
def ai_insights_page():
    if request.method == "POST":
        data = request.form
        insight = {
            "title": data.get("title"),
            "description": data.get("description")
        }
        mongo.db.ai_insights.insert_one(insight)
        return redirect(url_for("ai_insights_page"))

    # Fetch existing insights
    insights = list(mongo.db.ai_insights.find({}, {"_id": 0}))
    return render_template("ai_insights.html", insights=insights)

# ------------------------
# REGISTER WORKOUT API BLUEPRINT
# ------------------------
app.register_blueprint(workout_bp)

# ------------------------
# RUN APP
# ------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)