from flask import Blueprint, jsonify, render_template, session, redirect, url_for
from services.db import mongo
from google import genai
import os

ai_bp = Blueprint("ai", __name__)


# ------------------------
# GET RECENT USER DATA
# Gets only current user's data
# ------------------------
def get_recent_data():
    try:
        current_user = session.get("user")

        # Get latest 5 workouts for current user
        workouts = list(
            mongo.db.workouts.find(
                {"created_by": current_user},
                {"_id": 0}
            ).sort("_id", -1).limit(5)
        )

        # Get latest 5 meals for current user
        meals = list(
            mongo.db.meals.find(
                {"created_by": current_user},
                {"_id": 0}
            ).sort("_id", -1).limit(5)
        )

        # Get latest 5 sleeps for current user
        sleeps = list(
            mongo.db.sleeps.find(
                {"created_by": current_user},
                {"_id": 0}
            ).sort("_id", -1).limit(5)
        )

        return {
            "workouts": workouts,
            "meals": meals,
            "sleeps": sleeps,
            "db_status": "connected"
        }

    except Exception as e:
        return {
            "workouts": [],
            "meals": [],
            "sleeps": [],
            "db_status": f"disconnected: {str(e)}"
        }


# ------------------------
# BUILD PROMPT FOR GEMINI
# Sends real user data to AI
# ------------------------
def build_prompt(data):
    return f"""
You are a friendly wellness coach.

Analyze this user's recent health data and provide:

1. A short summary of their habits
2. 3 wellness insights
3. 3 simple goal suggestions

Rules:
- Keep the answer clear, short, and friendly
- Use simple English
- Base the answer only on the data provided
- If there is little data, say that gently
- Do not use complicated words

Workout data:
{data['workouts']}

Meal data:
{data['meals']}

Sleep data:
{data['sleeps']}
"""


# ------------------------
# FALLBACK RESPONSE
# Used if Gemini fails
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
# GENERATE GEMINI INSIGHTS
# ------------------------
def generate_gemini_insights(data):
    api_key = os.getenv("GEMINI_API_KEY")

    # If API key missing, use fallback
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
# ------------------------
@ai_bp.route("/ai_page")
def ai_page():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("ai_insights.html")


# ------------------------
# AI INSIGHTS API
# Returns JSON
# Also saves result in session
# ------------------------
@ai_bp.route("/ai/insights", methods=["GET"])
def insights():
    if "user" not in session:
        return jsonify({
            "status": "error",
            "message": "Unauthorized"
        }), 401

    data = get_recent_data()
    result = generate_gemini_insights(data)

    # Save insights so dashboard can show them
    session["ai_insights"] = result

    return jsonify({
        "status": "success",
        "insights": result,
        "data_used": data
    })


# ------------------------
# GENERATE + REDIRECT
# Better for button click
# ------------------------
@ai_bp.route("/generate-insights")
def generate_and_redirect():
    if "user" not in session:
        return redirect(url_for("login"))

    data = get_recent_data()
    result = generate_gemini_insights(data)

    # Save to session
    session["ai_insights"] = result

    # Go back to dashboard to show result
    return redirect(url_for("dashboard"))