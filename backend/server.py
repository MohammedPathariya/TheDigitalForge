# backend/server.py

from flask import Flask, request, jsonify
from main_deployment import DevelopmentCrew
import os

app = Flask(__name__)

@app.route("/run", methods=["POST"])
def run_pipeline():
    data = request.get_json()
    user_request = data.get("request", "")
    if not user_request:
        return jsonify({"error": "No request provided"}), 400

    try:
        crew = DevelopmentCrew(user_request)
        final_report = crew.run()
        return jsonify({"report": final_report})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)))