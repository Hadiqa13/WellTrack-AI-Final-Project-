from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from services.db import mongo
from routes.workout_routes import workout_bp

app = Flask(__name__)
app.config.from_object(Config)

CORS(app)
mongo.init_app(app)

@app.route("/")
def home():
    return jsonify({
        "message": "Health & Wellness Tracker API is running"
    }), 200

@app.route("/api/health")
def health_check():
    return jsonify({
        "status": "success",
        "message": "Backend is working"
    }), 200

@app.route("/test-db")
def test_db():
    mongo.db.test.insert_one({"name": "Asma"})
    return jsonify({"message": "Inserted successfully"}), 200

app.register_blueprint(workout_bp)

if __name__ == "__main__":
    app.run(debug=True)