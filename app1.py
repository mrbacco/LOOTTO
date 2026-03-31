# -*- coding: utf-8 -*-
"""
mrbacco copyright

This is a script file.
"""

import logging
import os
from flask import Flask, request, jsonify
from pymongo import MongoClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
logger.info(f"MongoDB URI: {MONGO_URI}")
client = MongoClient(MONGO_URI)
db = client["lottery"]
collection = db["lottoresults"]


@app.route("/")
def index():
    return jsonify({"status": "ok", "endpoints": ["/api/lottery?date=YYYY-MM-DD"]}), 200


@app.route("/api/lottery", methods=["GET"])
def get_lottery_results():
    try:
        date = request.args.get("date")
        limit = int(request.args.get("limit", 10))
        logger.info(f"Request received — date: {date}, limit: {limit}")

        if not date:
            logger.warning("Missing 'date' parameter — returning 400")
            return jsonify({"error": "Date parameter is required"}), 400

        query = {"_id": date} if date else {}

        cursor = (
            collection.find(query)
            .sort("drawDate", -1)
            .limit(limit)
        )

        results = list(cursor)
        logger.info(f"Query returned {len(results)} result(s) for date: {date}")

        if not results:
            logger.warning(f"No results found for date: {date} — returning 404")
            return jsonify({"error": "No results found"}), 404

        for doc in results:
            doc["_id"] = str(doc["_id"])

        return jsonify(results), 200

    except Exception as error:
        logger.error(f"Unexpected error: {error}", exc_info=True)
        return jsonify({
            "error": "Failed to fetch lottery results",
            "details": str(error)
        }), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting Flask app on port {port}")
    app.run(debug=True, port=port)