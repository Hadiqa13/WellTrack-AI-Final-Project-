from flask import Blueprint, jsonify, render_template, session, redirect, url_for
from services.db import mongo
from google import genai
import os

# Create AI blueprint
ai_bp = Blueprint("ai", __name__)


# ------------------------
# GET RECENT DATA FROM DATABASE
# Reads last few workout, meal, sleep records
# ------------------------
def get_recent_data():
    try:
        workouts = list(mongo.db.workouts.find({}, {"_id": 0}).limit(5))
        meals = list(mongo.db.meals.find({}, {"_id": 0}).limit(5))
        sleeps = list(mongo.db.sleeps.find({}, {"_id": 0}).limit(5))

        return {
            "workouts": workouts,
            "meals": meals,
            "sleeps": sleeps,
            "db_status": "connected"
        }

    except Exception:
        return {
            "workouts": [],
            "meals": [],
            "sleeps": [],
            "db_status": "disconnected"
        }


# ------------------------
# BUILD PROMPT FOR GEMINI
# Converts user health data into prompt text
# ------------------------
def build_prompt(data):
    return f"""
You are a wellness coach.

Analyze this user's recent health data and give:
1. A short summary of their habits
2. 3 wellness insights
3. 3 simple goal suggestions

Keep the answer clear, short, and friendly.

Workout data:
{data['workouts']}

Meal data:
{data['meals']}

Sleep data:
{data['sleeps']}
"""


# ------------------------
# FALLBACK RESPONSE
# Used if Gemini key missing or API fails
# ------------------------
def fallback_insights(data):
    workout_count = len(data["workouts"])
    meal_count = len(data["meals"])
    sleep_count = len(data["sleeps"])
    db_status = data.get("db_status", "unknown")

    return f"""
Summary:
You have {workout_count} workout records, {meal_count} meal records, and {sleep_count} sleep records.

Database status:
{db_status}

Insights:
1. Try to keep logging your habits regularly so the app can give better insights.
2. Balanced meals, regular workouts, and consistent sleep together improve wellness.
3. Small daily improvements are better than sudden big changes.

Goals:
1. Exercise at least 3 times this week.
2. Try to maintain a healthy meal routine.
3. Aim for a more consistent sleep schedule.
""".strip()


# ------------------------
# GENERATE AI INSIGHTS USING GEMINI
# ------------------------
def generate_gemini_insights(data):
    api_key = os.getenv("GEMINI_API_KEY")

    # If no key, use fallback response
    if not api_key:
        return fallback_insights(data)

    try:
        client = genai.Client(api_key=api_key)
        prompt = build_prompt(data)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        if response and getattr(response, "text", None):
            return response.text.strip()

        return fallback_insights(data)

    except Exception:
        return fallback_insights(data)


# ------------------------
# AI PAGE
# Protected page - must login first
# ------------------------
@ai_bp.route("/ai_page")
def ai_page():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("ai_insights.html")


# ------------------------
# AI INSIGHTS API
# Protected route - must login first
# ------------------------
@ai_bp.route("/ai/insights", methods=["GET"])
def insights():
    if "user" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    data = get_recent_data()
    result = generate_gemini_insights(data)

    return jsonify({
        "status": "success",
        "insights": result,
        "data_used": data
    })