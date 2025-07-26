# backend/server.py

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from main_deployment import DevelopmentCrew

app = Flask(__name__)
CORS(app)

@app.route("/run", methods=["POST"])
def run_pipeline():
    data = request.get_json() or {}
    user_request = data.get("request", "").strip()
    if not user_request:
        return jsonify({"error": "No request provided"}), 400

    crew = DevelopmentCrew(user_request)
    report = crew.run()
    return jsonify({"report": report}), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)