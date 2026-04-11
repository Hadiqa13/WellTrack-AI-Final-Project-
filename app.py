from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_cors import CORS
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId

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

# Load config
app.config.from_object(Config)

# Secret key for session
app.secret_key = app.config.get("SECRET_KEY", "mysecret123")

# Enable CORS
CORS(app)

# Connect MongoDB
mongo.init_app(app)


# ------------------------
# LOGIN REQUIRED DECORATOR
# ------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# ------------------------
# REGISTER PAGE
# ------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    success = None

    if request.method == "POST":
        full_name = request.form.get("full_name")
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if username exists
        existing_user = mongo.db.users.find_one({"username": username})

        if existing_user:
            error = "Username already exists. Please choose another one."
        else:
            hashed_password = generate_password_hash(password)

            user_data = {
                "full_name": full_name,
                "username": username,
                "email": email,
                "password": hashed_password
            }

            mongo.db.users.insert_one(user_data)
            success = "Registration successful. Please login."

    return render_template("register.html", error=error, success=success)


# ------------------------
# LOGIN PAGE
# ------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Find user
        user = mongo.db.users.find_one({"username": username})

        # Check password
        if user and check_password_hash(user["password"], password):
            session["user"] = user["username"]
            session["full_name"] = user.get("full_name", "")
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid username or password"

    return render_template("login.html", error=error)


# ------------------------
# LOGOUT
# ------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ------------------------
# HEALTH ENDPOINT
# ------------------------
@app.route("/api/health")
def health():
    return jsonify({"status": "success"})


# ------------------------
# DASHBOARD
# Show only current user's data
# ------------------------
@app.route("/")
@app.route("/dashboard")
@login_required
def dashboard():
    current_user = session.get("user")

    try:
        # Filter by logged-in user
        workouts = list(mongo.db.workouts.find({"created_by": current_user}))
        meals = list(mongo.db.meals.find({"created_by": current_user}))
        sleeps = list(mongo.db.sleeps.find({"created_by": current_user}))
    except Exception:
        workouts = []
        meals = []
        sleeps = []

    # Average workout duration
    avg_workout = round(
        sum(w.get("duration", 0) for w in workouts) / len(workouts), 2
    ) if workouts else 0

    # Average sleep duration
    avg_sleep = round(
        sum(s.get("duration", 0) for s in sleeps) / len(sleeps), 2
    ) if sleeps else 0

    # Get saved AI insights from session
    ai_insights = session.get("ai_insights", "")

    return render_template(
        "dashboard.html",
        workouts=workouts,
        meals=meals,
        sleeps=sleeps,
        avg_workout=avg_workout,
        avg_sleep=avg_sleep,
        ai_insights=ai_insights
    )


# ------------------------
# ADD WORKOUT PAGE
# ------------------------
@app.route("/add-workout", methods=["GET", "POST"])
@login_required
def add_workout_page():
    error = None

    if request.method == "POST":
        data = request.form

        workout = {
            "workout_type": data.get("workout_type"),
            "duration": int(data.get("duration")),
            "calories_burned": int(data.get("calories_burned", 0)),
            "date": data.get("date"),
            "created_by": session.get("user")
        }

        try:
            mongo.db.workouts.insert_one(workout)
            return redirect(url_for("dashboard"))
        except Exception:
            error = "Database connection failed. Please try again."

    return render_template("add_workout.html", error=error)


# ------------------------
# EDIT WORKOUT PAGE
# ------------------------
@app.route("/edit-workout/<id>", methods=["GET", "POST"])
@login_required
def edit_workout(id):
    workout = mongo.db.workouts.find_one({"_id": ObjectId(id)})

    if not workout:
        return "Workout not found", 404

    error = None

    if request.method == "POST":
        try:
            updated_workout = {
                "workout_type": request.form.get("workout_type"),
                "duration": int(request.form.get("duration")),
                "calories_burned": int(request.form.get("calories_burned", 0)),
                "date": request.form.get("date"),
                "created_by": session.get("user")
            }

            mongo.db.workouts.update_one(
                {"_id": ObjectId(id)},
                {"$set": updated_workout}
            )

            return redirect(url_for("dashboard"))
        except Exception:
            error = "Failed to update workout."

    return render_template("edit_workout.html", workout=workout, error=error)


# ------------------------
# DELETE WORKOUT
# ------------------------
@app.route("/delete-workout/<id>", methods=["POST"])
@login_required
def delete_workout(id):
    try:
        mongo.db.workouts.delete_one({"_id": ObjectId(id)})
        return redirect(url_for("dashboard"))
    except Exception:
        return "Failed to delete workout", 500


# ------------------------
# ADD MEAL PAGE
# ------------------------
@app.route("/add-meal", methods=["GET", "POST"])
@login_required
def add_meal_page():
    error = None

    if request.method == "POST":
        data = request.form

        meal = {
            "meal_type": data.get("meal_type"),
            "calories": int(data.get("calories")),
            "created_by": session.get("user")
        }

        try:
            mongo.db.meals.insert_one(meal)
            return redirect(url_for("dashboard"))
        except Exception:
            error = "Database connection failed. Please try again."

    return render_template("add_meal.html", error=error)


# ------------------------
# EDIT MEAL PAGE
# ------------------------
@app.route("/edit-meal/<id>", methods=["GET", "POST"])
@login_required
def edit_meal(id):
    meal = mongo.db.meals.find_one({"_id": ObjectId(id)})

    if not meal:
        return "Meal not found", 404

    error = None

    if request.method == "POST":
        try:
            updated_meal = {
                "meal_type": request.form.get("meal_type"),
                "calories": int(request.form.get("calories")),
                "created_by": session.get("user")
            }

            mongo.db.meals.update_one(
                {"_id": ObjectId(id)},
                {"$set": updated_meal}
            )

            return redirect(url_for("dashboard"))
        except Exception:
            error = "Failed to update meal."

    return render_template("edit_meal.html", meal=meal, error=error)


# ------------------------
# DELETE MEAL
# ------------------------
@app.route("/delete-meal/<id>", methods=["POST"])
@login_required
def delete_meal(id):
    try:
        mongo.db.meals.delete_one({"_id": ObjectId(id)})
        return redirect(url_for("dashboard"))
    except Exception:
        return "Failed to delete meal", 500


# ------------------------
# ADD SLEEP PAGE
# ------------------------
@app.route("/add-sleep", methods=["GET", "POST"])
@login_required
def add_sleep_page():
    error = None

    if request.method == "POST":
        data = request.form

        sleep = {
            "duration": float(data.get("duration")),
            "quality": data.get("quality"),
            "created_by": session.get("user")
        }

        try:
            mongo.db.sleeps.insert_one(sleep)
            return redirect(url_for("dashboard"))
        except Exception:
            error = "Database connection failed. Please try again."

    return render_template("add_sleep.html", error=error)


# ------------------------
# EDIT SLEEP PAGE
# ------------------------
@app.route("/edit-sleep/<id>", methods=["GET", "POST"])
@login_required
def edit_sleep(id):
    sleep = mongo.db.sleeps.find_one({"_id": ObjectId(id)})

    if not sleep:
        return "Sleep record not found", 404

    error = None

    if request.method == "POST":
        try:
            updated_sleep = {
                "duration": float(request.form.get("duration")),
                "quality": request.form.get("quality"),
                "created_by": session.get("user")
            }

            mongo.db.sleeps.update_one(
                {"_id": ObjectId(id)},
                {"$set": updated_sleep}
            )

            return redirect(url_for("dashboard"))
        except Exception:
            error = "Failed to update sleep record."

    return render_template("edit_sleep.html", sleep=sleep, error=error)


# ------------------------
# DELETE SLEEP
# ------------------------
@app.route("/delete-sleep/<id>", methods=["POST"])
@login_required
def delete_sleep(id):
    try:
        mongo.db.sleeps.delete_one({"_id": ObjectId(id)})
        return redirect(url_for("dashboard"))
    except Exception:
        return "Failed to delete sleep record", 500


# ------------------------
# REGISTER BLUEPRINTS
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