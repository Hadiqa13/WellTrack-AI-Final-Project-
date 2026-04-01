from flask import Blueprint, jsonify, request
from services.db import mongo

sleep_bp = Blueprint("sleep_bp", __name__)

# Get all sleep records
@sleep_bp.route("/api/sleeps", methods=["GET"])
def get_sleeps():
    sleeps = list(mongo.db.sleeps.find({}, {"_id": 0}))
    return jsonify(sleeps), 200

# Add a sleep record
@sleep_bp.route("/api/sleeps", methods=["POST"])
def add_sleep():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    sleep = {
        "duration": data.get("duration"),
        "quality": data.get("quality"),
        "date": data.get("date")
    }

    if not sleep["duration"] or not sleep["quality"] or not sleep["date"]:
        return jsonify({
            "error": "duration, quality, and date are required"
        }), 400

    mongo.db.sleeps.insert_one(sleep)

    return jsonify({
        "message": "Sleep record added successfully",
        "data": sleep
    }), 201