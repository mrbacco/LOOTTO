# -*- coding: utf-8 -*-
"""
mrbacco04 copyright

This is a script file.
"""

import logging
import os
import csv
from datetime import date, datetime
from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, PyMongoError, ServerSelectionTimeoutError
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
BAC_LOG = logging.getLogger(__name__)

app = Flask(__name__)

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    mongo_user = os.getenv("MONGO_USER", "mrbacco04_db_user")
    mongo_password = os.getenv("MONGO_PASSWORD", "wdTWUwfeVRB7aIlD")
    mongo_host = os.getenv("MONGO_HOST", "cluster0.cxzgfix.mongodb.net")
    mongo_app = os.getenv("MONGO_APP_NAME", "Cluster0")
    MONGO_URI = f"mongodb+srv://{mongo_user}:{mongo_password}@{mongo_host}/?appName={mongo_app}"

BAC_LOG.info("Using MongoDB Atlas URI from environment")
BAC_LOG.debug(f"MongoDB Atlas URI: {MONGO_URI}")
client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=10000,
    socketTimeoutMS=10000,
    server_api=ServerApi('1')
)
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
        BAC_LOG.debug("MongoDB ping successful")
        return True
    except ServerSelectionTimeoutError as error:
        BAC_LOG.warning(f"MongoDB ping timeout: {error}")
        return False
    except PyMongoError as error:
        BAC_LOG.error(f"MongoDB ping failed: {error}", exc_info=True)
        return False


def get_csv_lottery_results(date_filter=None, limit=10):
    results = []

    if not os.path.exists(CSV_FILE):
        BAC_LOG.warning(f"CSV fallback file missing: {CSV_FILE}")
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


def validate_lottery_payload(data):
    if not isinstance(data, dict):
        return "Request body must be a JSON object"

    required = ["drawDate", "num1", "num2", "num3", "num4", "num5", "num6", "strong"]
    for field in required:
        if field not in data:
            return f"Missing required field: {field}"
        if data[field] is None or str(data[field]).strip() == "":
            return f"Field {field} cannot be empty"

    try:
        datetime.fromisoformat(data["drawDate"])
    except ValueError:
        return "drawDate must be in ISO format YYYY-MM-DD"

    return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    db_status = "up" if is_database_available() else "down"
    active_source = "mongodb" if db_status == "up" else "csv-fallback"
    BAC_LOG.info(f"Health check requested: database={db_status}, active_source={active_source}")
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
            limit = int(request.args.get("limit", 50))
        except (TypeError, ValueError):
            return jsonify({"error": "limit must be an integer"}), 400

        if limit < 1:
            return jsonify({"error": "limit must be >= 1"}), 400

        BAC_LOG.info(f"Request received — date: {date}, limit: {limit}")

        if not is_database_available():
            BAC_LOG.warning("MongoDB unavailable; serving results from CSV fallback")
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
        BAC_LOG.info(f"Query returned {len(results)} result(s) for date: {date or 'latest'}")

        if not results:
            BAC_LOG.warning(f"No results found for date: {date} — returning 404")
            return jsonify({"error": "No results found"}), 404

        return jsonify(make_json_safe(results)), 200

    except PyMongoError as error:
        BAC_LOG.error(f"MongoDB error: {error}", exc_info=True)
        return jsonify({
            "error": "Database query failed",
            "details": str(error)
        }), 503

    except Exception as error:
        BAC_LOG.error(f"Unexpected error: {error}", exc_info=True)
        return jsonify({
            "error": "Failed to fetch lottery results",
            "details": str(error)
        }), 500


@app.route("/api/lottery/<draw_date>", methods=["GET"])
def get_lottery_result(draw_date):
    try:
        BAC_LOG.info(f"Fetching single result for {draw_date}")
        result = collection.find_one({"_id": draw_date})
        if not result:
            return jsonify({"error": "Result not found"}), 404
        return jsonify(make_json_safe(result)), 200
    except PyMongoError as error:
        BAC_LOG.error(f"MongoDB error: {error}", exc_info=True)
        return jsonify({"error": "Database query failed", "details": str(error)}), 503
    except Exception as error:
        BAC_LOG.error(f"Unexpected error: {error}", exc_info=True)
        return jsonify({"error": "Failed to fetch result", "details": str(error)}), 500


@app.route("/api/lottery", methods=["POST"])
def create_lottery_result():
    if not request.is_json:
        BAC_LOG.warning("Create lottery result failed: request body is not JSON")
        return jsonify({"error": "Request body must be JSON"}), 400

    data = request.get_json()
    error_message = validate_lottery_payload(data)
    if error_message:
        BAC_LOG.warning(f"Create lottery result validation failed: {error_message}")
        return jsonify({"error": error_message}), 400

    document = {
        "_id": data["drawDate"],
        "drawDate": data["drawDate"],
        "num1": str(data["num1"]).strip(),
        "num2": str(data["num2"]).strip(),
        "num3": str(data["num3"]).strip(),
        "num4": str(data["num4"]).strip(),
        "num5": str(data["num5"]).strip(),
        "num6": str(data["num6"]).strip(),
        "strong": str(data["strong"]).strip(),
        "source": data.get("source", "api")
    }

    try:
        collection.insert_one(document)
        BAC_LOG.info(f"Created new lottery result for {data['drawDate']}")
        return jsonify(make_json_safe(document)), 201
    except DuplicateKeyError:
        return jsonify({"error": "Lottery result already exists"}), 409
    except PyMongoError as error:
        BAC_LOG.error(f"MongoDB error: {error}", exc_info=True)
        return jsonify({"error": "Database insert failed", "details": str(error)}), 503
    except Exception as error:
        BAC_LOG.error(f"Unexpected error: {error}", exc_info=True)
        return jsonify({"error": "Failed to create result", "details": str(error)}), 500


@app.route("/api/lottery/<draw_date>", methods=["PUT"])
def update_lottery_result(draw_date):
    if not request.is_json:
        BAC_LOG.warning(f"Update failed for {draw_date}: request body is not JSON")
        return jsonify({"error": "Request body must be JSON"}), 400

    data = request.get_json()
    error_message = validate_lottery_payload(data)
    if error_message:
        BAC_LOG.warning(f"Update validation failed for {draw_date}: {error_message}")
        return jsonify({"error": error_message}), 400

    update_fields = {
        "drawDate": data["drawDate"],
        "num1": str(data["num1"]).strip(),
        "num2": str(data["num2"]).strip(),
        "num3": str(data["num3"]).strip(),
        "num4": str(data["num4"]).strip(),
        "num5": str(data["num5"]).strip(),
        "num6": str(data["num6"]).strip(),
        "strong": str(data["strong"]).strip(),
        "source": data.get("source", "api")
    }

    try:
        result = collection.update_one(
            {"_id": draw_date},
            {"$set": update_fields}
        )
        if result.matched_count == 0:
            return jsonify({"error": "Result not found"}), 404
        BAC_LOG.info(f"Updated lottery result for {draw_date}")
        return jsonify({"message": "Result updated successfully"}), 200
    except PyMongoError as error:
        BAC_LOG.error(f"MongoDB error: {error}", exc_info=True)
        return jsonify({"error": "Database update failed", "details": str(error)}), 503
    except Exception as error:
        BAC_LOG.error(f"Unexpected error: {error}", exc_info=True)
        return jsonify({"error": "Failed to update result", "details": str(error)}), 500


@app.route("/api/lottery/<draw_date>", methods=["DELETE"])
def delete_lottery_result(draw_date):
    try:
        result = collection.delete_one({"_id": draw_date})
        if result.deleted_count == 0:
            return jsonify({"error": "Result not found"}), 404
        BAC_LOG.info(f"Deleted lottery result for {draw_date}")
        return jsonify({"message": "Result deleted successfully"}), 200
    except PyMongoError as error:
        BAC_LOG.error(f"MongoDB error: {error}", exc_info=True)
        return jsonify({"error": "Database delete failed", "details": str(error)}), 503
    except Exception as error:
        BAC_LOG.error(f"Unexpected error: {error}", exc_info=True)
        return jsonify({"error": "Failed to delete result", "details": str(error)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    BAC_LOG.info(f"Starting Flask app on port {port}")
    app.run(debug=True, port=port)
    port = int(os.getenv("PORT", 8000))
    BAC_LOG.info(f"Starting Flask app on port {port}")
    app.run(debug=True, port=port)