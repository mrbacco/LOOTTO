# -*- coding: utf-8 -*-
"""
mrbacco copyright

This is a script file.
"""

import logging
import os
import csv
from datetime import date, datetime
from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
logger.info(f"MongoDB URI: {MONGO_URI}")
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
db = client["lottery"]
collection = db["lottoresults"]
CSV_FILE = os.path.join(os.path.dirname(__file__), "Lotto.csv")


def make_json_safe(value):
    if isinstance(value, dict):
        return {k: make_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [make_json_safe(v) for v in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    # Handle common MongoDB/BSON objects (ObjectId, Decimal128, etc.).
    return str(value)


def is_database_available():
    try:
        client.admin.command("ping")
        return True
    except ServerSelectionTimeoutError:
        return False
    except PyMongoError:
        return False


def get_csv_lottery_results(date_filter=None, limit=10):
    results = []

    if not os.path.exists(CSV_FILE):
        return results

    with open(CSV_FILE, "r", encoding="latin-1", newline="") as csv_file:
        reader = csv.reader(csv_file)
        next(reader, None)

        for row in reader:
            if len(row) < 9:
                continue

            raw_date = row[1].strip()
            try:
                draw_date = datetime.strptime(raw_date, "%d/%m/%Y").date()
            except ValueError:
                continue

            iso_date = draw_date.isoformat()
            if date_filter and iso_date != date_filter:
                continue

            result = {
                "_id": iso_date,
                "drawDate": iso_date,
                "num1": row[2].strip(),
                "num2": row[3].strip(),
                "num3": row[4].strip(),
                "num4": row[5].strip(),
                "num5": row[6].strip(),
                "num6": row[7].strip(),
                "strong": row[8].strip(),
                "source": "csv"
            }
            results.append(result)

    results.sort(key=lambda item: item["drawDate"], reverse=True)
    return results[:limit]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    db_status = "up" if is_database_available() else "down"
    active_source = "mongodb" if db_status == "up" else "csv-fallback"
    return jsonify({
        "status": "ok",
        "database": db_status,
        "active_source": active_source,
        "endpoints": ["/api/lottery?date=YYYY-MM-DD&limit=10"]
    }), 200


@app.route("/api/lottery", methods=["GET"])
def get_lottery_results():
    try:
        date = request.args.get("date")
        try:
            limit = int(request.args.get("limit", 10))
        except (TypeError, ValueError):
            return jsonify({"error": "limit must be an integer"}), 400

        if limit < 1:
            return jsonify({"error": "limit must be >= 1"}), 400

        logger.info(f"Request received — date: {date}, limit: {limit}")

        if not is_database_available():
            logger.warning("MongoDB unavailable; serving results from CSV fallback")
            csv_results = get_csv_lottery_results(date_filter=date, limit=limit)
            if not csv_results:
                return jsonify({"error": "No results found"}), 404
            return jsonify(csv_results), 200

        query = {"_id": date} if date else {}

        cursor = (
            collection.find(query)
            .sort("drawDate", -1)
            .limit(limit)
        )

        results = list(cursor)
        logger.info(f"Query returned {len(results)} result(s) for date: {date or 'latest'}")

        if not results:
            logger.warning(f"No results found for date: {date} — returning 404")
            return jsonify({"error": "No results found"}), 404

        return jsonify(make_json_safe(results)), 200

    except PyMongoError as error:
        logger.error(f"MongoDB error: {error}", exc_info=True)
        return jsonify({
            "error": "Database query failed",
            "details": str(error)
        }), 503

    except Exception as error:
        logger.error(f"Unexpected error: {error}", exc_info=True)
        return jsonify({
            "error": "Failed to fetch lottery results",
            "details": str(error)
        }), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting Flask app on port {port}")
    app.run(debug=True, port=port)