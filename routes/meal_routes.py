from flask import Blueprint, jsonify, request
from services.db import mongo

meal_bp = Blueprint("meal_bp", __name__)

# GET meals
@meal_bp.route("/api/meals", methods=["GET"])
def get_meals():
    meals = list(mongo.db.meals.find({}, {"_id": 0}))
    return jsonify(meals), 200

# POST meal
@meal_bp.route("/api/meals", methods=["POST"])
def add_meal():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    meal = {
        "meal_name": data.get("meal_name"),
        "calories": data.get("calories"),
        "date": data.get("date")
    }

    if not meal["meal_name"] or not meal["calories"] or not meal["date"]:
        return jsonify({
            "error": "meal_name, calories, and date are required"
        }), 400

    mongo.db.meals.insert_one(meal)

    return jsonify({
        "message": "Meal added successfully",
        "data": meal
    }), 201