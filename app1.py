# -*- coding: utf-8 -*-
"""
mrbacco copyright

This is a script file.
"""

import logging
import os
from flask import Flask, request, jsonify, render_template_string
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

UI_HTML = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>LOOTTO Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css" integrity="sha512-SnH5WK+bZxgPHs44uWix+LLJAJ9/2PkPKZ5QiAj6Ta86w+fsb2TkR4j8R2AB1z7Wmim8O0P6bR9N7f4l6L7w6w==" crossorigin="anonymous" referrerpolicy="no-referrer" />
    <style>
        :root {
            --bg: #f5f0e7;
            --panel: #fffdf8;
            --ink: #15202b;
            --muted: #4f5b66;
            --brand: #0b7a75;
            --brand-2: #f59e0b;
            --line: #e6ded0;
            --ok: #0f766e;
            --err: #b42318;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            min-height: 100vh;
            font-family: "Space Grotesk", sans-serif;
            color: var(--ink);
            background:
                radial-gradient(circle at 15% 0%, #fff5dc 0%, transparent 35%),
                radial-gradient(circle at 100% 30%, #dff7f5 0%, transparent 30%),
                linear-gradient(160deg, #f5f0e7 0%, #f8fbff 100%);
            display: grid;
            place-items: center;
            padding: 24px;
        }
        .card {
            width: min(960px, 100%);
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 20px;
            box-shadow: 0 20px 48px rgba(21, 32, 43, 0.12);
            overflow: hidden;
            animation: rise 0.45s ease-out;
        }
        .head {
            padding: 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            border-bottom: 1px solid var(--line);
            background: linear-gradient(120deg, rgba(11, 122, 117, 0.09), rgba(245, 158, 11, 0.08));
        }
        .title {
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 0;
            font-size: 1.6rem;
            font-weight: 700;
            letter-spacing: 0.2px;
        }
        .title i { color: var(--brand); }
        .subtitle {
            margin: 6px 0 0;
            color: var(--muted);
            font-size: 0.95rem;
        }
        .grid {
            padding: 22px;
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 14px;
        }
        .field {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        label {
            font-size: 0.85rem;
            color: var(--muted);
            font-weight: 600;
        }
        input {
            border: 1px solid #d7ccba;
            border-radius: 12px;
            padding: 12px 13px;
            font: inherit;
            background: #ffffff;
            color: var(--ink);
        }
        input:focus {
            outline: none;
            border-color: var(--brand);
            box-shadow: 0 0 0 4px rgba(11, 122, 117, 0.13);
        }
        .actions {
            padding: 0 22px 22px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        button {
            border: none;
            border-radius: 12px;
            padding: 11px 15px;
            font: inherit;
            font-weight: 700;
            cursor: pointer;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        button:hover {
            transform: translateY(-1px);
            box-shadow: 0 10px 18px rgba(21, 32, 43, 0.14);
        }
        .btn-primary {
            background: linear-gradient(100deg, #0b7a75, #12a39c);
            color: #ffffff;
        }
        .btn-ghost {
            background: #fff8ea;
            color: #7c4a00;
            border: 1px solid #f7d9a6;
        }
        .status {
            padding: 0 22px 14px;
            min-height: 26px;
            color: var(--muted);
            font-weight: 600;
        }
        .status.ok { color: var(--ok); }
        .status.err { color: var(--err); }
        .results {
            margin: 0 22px 22px;
            border: 1px solid var(--line);
            border-radius: 14px;
            background: #ffffff;
            overflow: hidden;
        }
        .results-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            padding: 10px 14px;
            background: #f8f3ea;
            border-bottom: 1px solid var(--line);
            font-size: 0.9rem;
            color: var(--muted);
        }
        pre {
            margin: 0;
            padding: 15px;
            min-height: 210px;
            max-height: 420px;
            overflow: auto;
            background: #fff;
            font-size: 0.9rem;
            line-height: 1.45;
        }
        @keyframes rise {
            from { opacity: 0; transform: translateY(12px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @media (max-width: 820px) {
            .grid { grid-template-columns: 1fr; }
            .head { flex-direction: column; align-items: flex-start; }
        }
    </style>
</head>
<body>
    <main class="card">
        <section class="head">
            <div>
                <h1 class="title"><i class="fa-solid fa-clover"></i> LOOTTO Dashboard</h1>
                <p class="subtitle">Search lottery results by draw date and preview JSON instantly.</p>
            </div>
            <div>
                <button id="healthBtn" class="btn-ghost" type="button"><i class="fa-solid fa-heart-pulse"></i> Health Check</button>
            </div>
        </section>

        <section class="grid">
            <div class="field">
                <label for="date"><i class="fa-regular fa-calendar"></i> Draw Date</label>
                <input id="date" type="date" />
            </div>
            <div class="field">
                <label for="limit"><i class="fa-solid fa-list-ol"></i> Limit</label>
                <input id="limit" type="number" min="1" max="100" value="10" />
            </div>
            <div class="field">
                <label for="endpoint"><i class="fa-solid fa-link"></i> Endpoint</label>
                <input id="endpoint" type="text" value="/api/lottery" readonly />
            </div>
        </section>

        <section class="actions">
            <button id="searchBtn" class="btn-primary" type="button"><i class="fa-solid fa-magnifying-glass"></i> Search Results</button>
            <button id="clearBtn" class="btn-ghost" type="button"><i class="fa-solid fa-broom"></i> Clear</button>
        </section>

        <div id="status" class="status">Ready.</div>

        <section class="results">
            <div class="results-head">
                <span><i class="fa-solid fa-database"></i> Response Preview</span>
            </div>
            <pre id="output">Run a search to display API results.</pre>
        </section>
    </main>

    <script>
        const dateEl = document.getElementById("date");
        const limitEl = document.getElementById("limit");
        const outputEl = document.getElementById("output");
        const statusEl = document.getElementById("status");
        const searchBtn = document.getElementById("searchBtn");
        const clearBtn = document.getElementById("clearBtn");
        const healthBtn = document.getElementById("healthBtn");

        function setStatus(message, type) {
            statusEl.textContent = message;
            statusEl.className = "status" + (type ? " " + type : "");
        }

        async function callApi(url) {
            setStatus("Loading...", "");
            outputEl.textContent = "Fetching...";
            try {
                const res = await fetch(url);
                const data = await res.json();
                outputEl.textContent = JSON.stringify(data, null, 2);
                if (res.ok) {
                    setStatus("Success: " + res.status, "ok");
                } else {
                    setStatus("Request failed: " + res.status, "err");
                }
            } catch (err) {
                outputEl.textContent = String(err);
                setStatus("Network error", "err");
            }
        }

        searchBtn.addEventListener("click", async () => {
            const limit = Number(limitEl.value || 10);
            const datePart = dateEl.value ? "date=" + encodeURIComponent(dateEl.value) + "&" : "";
            const url = "/api/lottery?" + datePart + "limit=" + encodeURIComponent(limit);
            await callApi(url);
        });

        clearBtn.addEventListener("click", () => {
            dateEl.value = "";
            limitEl.value = 10;
            outputEl.textContent = "Run a search to display API results.";
            setStatus("Ready.", "");
        });

        healthBtn.addEventListener("click", async () => {
            await callApi("/health");
        });
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(UI_HTML)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "endpoints": ["/api/lottery?date=YYYY-MM-DD&limit=10"]}), 200


@app.route("/api/lottery", methods=["GET"])
def get_lottery_results():
    try:
        date = request.args.get("date")
        limit = int(request.args.get("limit", 10))
        logger.info(f"Request received — date: {date}, limit: {limit}")

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
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting Flask app on port {port}")
    app.run(debug=True, port=port)