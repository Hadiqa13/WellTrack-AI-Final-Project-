from flask import Blueprint, jsonify, request
from services.db import mongo

workout_bp = Blueprint("workout_bp", __name__)

@workout_bp.route("/api/workouts", methods=["GET"])
def get_workouts():
    workouts = list(mongo.db.workouts.find({}, {"_id": 0}))
    return jsonify(workouts), 200

@workout_bp.route("/api/workouts", methods=["POST"])
def add_workout():
    data = request.get_json()

    workout = {
        "workout_type": data.get("workout_type"),
        "duration": data.get("duration"),
        "calories_burned": data.get("calories_burned"),
        "date": data.get("date")
    }

    mongo.db.workouts.insert_one(workout)

    return jsonify({
        "message": "Workout added successfully",
        "data": workout
    }), 201