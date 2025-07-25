# backend/server.py
from flask import Flask, request, jsonify
from main_deployment import DevelopmentCrew
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/run', methods=['POST'])
def run_pipeline():
    data = request.json
    user_request = data.get("request", "")
    if not user_request.strip():
        return jsonify({"error": "Request is empty"}), 400

    crew = DevelopmentCrew(user_request)
    full_report = crew.run_pipeline()

    return jsonify({"report": f"<pre>{full_report}</pre>"}), 200
