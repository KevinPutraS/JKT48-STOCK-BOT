import os
import json
import threading
import time

from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__)

socketio = SocketIO(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CACHE_FILE = os.path.join(BASE_DIR, "stock_cache.json")


def load_cache():

    if not os.path.exists(CACHE_FILE):
        return {}

    try:

        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except:
        return {}


@app.route("/")
def home():

    return """
    <html>

    <head>

        <title>JKT48 Dashboard</title>

        <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>

        <style>

            *{
                margin:0;
                padding:0;
                box-sizing:border-box;
            }

            body{
                background:#020617;
                color:white;
                font-family:Arial,sans-serif;
                padding:30px;
            }

            .topbar{
                margin-bottom:30px;
            }

            .title{
                font-size:42px;
                font-weight:bold;
                color:#38bdf8;
            }

            .subtitle{
                color:#94a3b8;
                margin-top:10px;
            }

            .grid{
                display:grid;
                grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
                gap:20px;
            }

            .card{
                background:#0f172a;
                border:1px solid #1e293b;
                border-radius:22px;
                padding:22px;
                transition:0.2s;
            }

            .card:hover{
                transform:translateY(-4px);
                border-color:#38bdf8;
            }

            .member{
                font-size:26px;
                font-weight:bold;
                margin-bottom:14px;
            }

            .category{
                color:#facc15;
                margin-bottom:10px;
                font-size:15px;
            }

            .session{
                color:#94a3b8;
                margin-bottom:18px;
            }

            .stock{
                font-size:52px;
                font-weight:bold;
                color:#22c55e;
            }

            .low{
                color:#f59e0b;
            }

            .soldout{
                color:#ef4444;
            }

            .badge{
                display:inline-block;
                margin-top:14px;
                padding:8px 14px;
                border-radius:999px;
                background:#1e293b;
                font-size:12px;
                font-weight:bold;
            }

        </style>

    </head>

    <body>

        <div class="topbar">

            <div class="title">
                🚀 JKT48 REALTIME DASHBOARD
            </div>

            <div class="subtitle">
                Live realtime stock monitoring
            </div>

        </div>

        <div style="display:flex;gap:15px;margin-bottom:25px;flex-wrap:wrap;">

            <input
                type="text"
                id="search"
                placeholder="Cari member..."
                style="
                    flex:1;
                    min-width:220px;
                    padding:14px;
                    border:none;
                    border-radius:14px;
                    background:#0f172a;
                    color:white;
                    font-size:15px;
                    border:1px solid #1e293b;
                "
            >

            <select
                id="memberFilter"
                style="
                    padding:14px;
                    border:none;
                    border-radius:14px;
                    background:#0f172a;
                    color:white;
                    font-size:15px;
                    border:1px solid #1e293b;
                "
            >
                <option value="">All Members</option>
            </select>

            <select
                id="categoryFilter"
                style="
                    padding:14px;
                    border:none;
                    border-radius:14px;
                    background:#0f172a;
                    color:white;
                    font-size:15px;
                    border:1px solid #1e293b;
                "
            >
                <option value="">All Categories</option>
            </select>

        </div>

        <div id="grid" class="grid"></div>

        <script>

        const socket = io();

        socket.emit("request_data");

        let globalData = {};

        const searchInput = document.getElementById("search");

        const memberFilter = document.getElementById("memberFilter");

        const categoryFilter = document.getElementById("categoryFilter");


        function renderCards(data){

            let grid = document.getElementById("grid");

            grid.innerHTML = "";

            let search = searchInput.value.toLowerCase();

            let selectedMember =
                memberFilter.value.toLowerCase();

            let selectedCategory =
                categoryFilter.value.toLowerCase();

            Object.entries(data).forEach(([key, quota]) => {

                let parts = key.split("|||");

                let category =
                    parts[0] || "EVENT";

                let eventCode =
                    parts[1] || "UNKNOWN";

                let member =
                    parts[2] || "UNKNOWN";

                let session =
                    parts[3] || "UNKNOWN";

                if(
                    search &&
                    !member.toLowerCase().includes(search)
                ){
                    return;
                }

                if(
                    selectedMember &&
                    member.toLowerCase() !== selectedMember
                ){
                    return;
                }

                if(
                    selectedCategory &&
                    category.toLowerCase() !== selectedCategory
                ){
                    return;
                }

                let stockClass = "stock";

                let badge = "AVAILABLE";

                if(quota <= 2 && quota > 0){

                    stockClass += " low";

                    badge = "LOW STOCK";
                }

                if(quota == 0){

                    stockClass = "stock soldout";

                    badge = "SOLD OUT";
                }

                grid.innerHTML += `
                
                <div class="card">

                    <div class="member">
                        ⭐ ${member}
                    </div>

                    <div class="category">
                        📁 ${category}
                    </div>

                    <div class="session">
                        🎫 ${session}
                    </div>

                    <div class="${stockClass}">
                        ${quota}
                    </div>

                    <div class="badge">
                        ${badge}
                    </div>

                </div>
                `;
            });
        }


        socket.on("update", (data) => {

            globalData = data;

            let members = new Set();

            let categories = new Set();

            Object.entries(data).forEach(([key, quota]) => {

                let parts = key.split("|||");

                let category =
                    parts[0] || "EVENT";

                let member =
                    parts[2] || "UNKNOWN";

                members.add(member);

                categories.add(category);

            });

            memberFilter.innerHTML =
                `<option value="">All Members</option>`;

            [...members]
            .sort()
            .forEach(member => {

                memberFilter.innerHTML += `
                    <option value="${member}">
                        ${member}
                    </option>
                `;
            });


            categoryFilter.innerHTML =
                `<option value="">All Categories</option>`;

            [...categories]
            .sort()
            .forEach(category => {

                categoryFilter.innerHTML += `
                    <option value="${category}">
                        ${category}
                    </option>
                `;
            });

            renderCards(globalData);

        });


        searchInput.addEventListener("input", () => {

            renderCards(globalData);

        });

        memberFilter.addEventListener("change", () => {

            renderCards(globalData);

        });

        categoryFilter.addEventListener("change", () => {

            renderCards(globalData);

        });

        </script>

    </body>

    </html>
    """


@socketio.on("request_data")
def send_initial_data():

    data = load_cache()

    emit("update", data)


def background_update():

    old_data = {}

    while True:

        data = load_cache()

        if data != old_data:

            socketio.emit("update", data)

            old_data = data

        time.sleep(2)


if __name__ == "__main__":

    thread = threading.Thread(target=background_update)

    thread.daemon = True

    thread.start()

    socketio.run(
        app,
        debug=True,
        port=5000
    )