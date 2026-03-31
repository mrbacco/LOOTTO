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
