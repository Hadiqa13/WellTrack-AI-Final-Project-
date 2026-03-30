from flask import Blueprint, jsonify, request
from services.db import mongo

workout_bp = Blueprint("workout_bp", __name__)

# Get all workouts (API)
@workout_bp.route("/api/workouts", methods=["GET"])
def get_workouts():
    workouts = list(mongo.db.workouts.find({}, {"_id": 0}))
    return jsonify(workouts), 200

# Add a new workout (API)
@workout_bp.route("/api/workouts", methods=["POST"])
def add_workout():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    workout = {
        "workout_type": data.get("workout_type"),
        "duration": data.get("duration"),
        "calories_burned": data.get("calories_burned", 0),
        "date": data.get("date")
    }

    # Required fields validation
    if not workout["workout_type"] or not workout["duration"] or not workout["date"]:
        return jsonify({
            "error": "workout_type, duration, and date are required"
        }), 400

    mongo.db.workouts.insert_one(workout)

    return jsonify({
        "message": "Workout added successfully",
        "data": workout
    }), 201