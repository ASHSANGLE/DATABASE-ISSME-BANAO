from flask import Flask, render_template, request, jsonify, session, redirect
from copy import deepcopy

app = Flask(__name__)
app.secret_key = "change_this_secret_key"

# Store games in memory (per user)
user_games = {}

# ===============================
# GRID GENERATORS
# ===============================

def generate_4x4():
    return [
        [1, 0, 0, 4],
        [0, 4, 1, 0],
        [0, 1, 3, 0],
        [4, 0, 0, 2]
    ]

def generate_9x9():
    return [
        [5,3,0,0,7,0,0,0,0],
        [6,0,0,1,9,5,0,0,0],
        [0,9,8,0,0,0,0,6,0],
        [8,0,0,0,6,0,0,0,3],
        [4,0,0,8,0,3,0,0,1],
        [7,0,0,0,2,0,0,0,6],
        [0,6,0,0,0,0,2,8,0],
        [0,0,0,4,1,9,0,0,5],
        [0,0,0,0,8,0,0,7,9]
    ]

def generate_grid(size):
    if size == 9:
        return deepcopy(generate_9x9())
    return deepcopy(generate_4x4())

# ===============================
# VALIDATION
# ===============================

def can_place(grid, row, col, num, size):

    # Row check
    if num in grid[row]:
        return False

    # Column check
    for i in range(size):
        if grid[i][col] == num:
            return False

    # Box check
    box_size = int(size ** 0.5)
    start_row = (row // box_size) * box_size
    start_col = (col // box_size) * box_size

    for i in range(box_size):
        for j in range(box_size):
            if grid[start_row + i][start_col + j] == num:
                return False

    return True

# ===============================
# ROUTES
# ===============================

@app.route("/")
def home():
    return redirect("/login")

@app.route("/login")
def login():
    # Demo login (replace with real login in Golden Sage)
    session["user_id"] = "demo_user"
    return redirect("/sudoku")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/sudoku")
def sudoku():

    if "user_id" not in session:
        return redirect("/login")

    size = request.args.get("size", 4, type=int)
    user_id = session["user_id"]

    # Create new game if not exists or grid size changed
    if user_id not in user_games or user_games[user_id]["size"] != size:
        grid = generate_grid(size)
        user_games[user_id] = {
            "size": size,
            "grid": grid,
            "original": deepcopy(grid)
        }

    game = user_games[user_id]

    return render_template(
        "sudoku.html",
        grid=game["grid"],
        size=size
    )

@app.route("/check", methods=["POST"])
def check():

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"})

    user_id = session["user_id"]
    data = request.json

    row = data["row"]
    col = data["col"]
    num = data["num"]

    game = user_games.get(user_id)

    if not game:
        return jsonify({"status": "error"})

    grid = game["grid"]
    original = game["original"]
    size = game["size"]

    # Prevent editing original cells
    if original[row][col] != 0:
        return jsonify({"status": "blocked"})

    if can_place(grid, row, col, num, size):
        grid[row][col] = num
        return jsonify({"status": "correct"})
    else:
        return jsonify({"status": "wrong"})

# ===============================
# RUN
# ===============================

if __name__ == "__main__":
    app.run(debug=True)
