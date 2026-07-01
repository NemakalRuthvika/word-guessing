import os
import random
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# Environment variables లోడ్ చేయడం
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY", "wordquest-change-me-in-production"
)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

# --- మోంగోడిబి కనెక్షన్ సెటప్ ---
DEFAULT_MONGODB_URI = "mongodb://localhost:27017/"
MONGODB_URI = (
    os.environ.get("MONGODB_URI")
    or os.environ.get("MONGO_URI")
    or DEFAULT_MONGODB_URI
)
MONGODB_DB_NAME = (
    os.environ.get("MONGODB_DB_NAME")
    or os.environ.get("MONGO_DATABASE")
    or "wordquest"
)

try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    
    client.admin.command("ping")
    mongo_db = client[MONGODB_DB_NAME]
    words_collection = mongo_db["words"]
    games_collection = mongo_db["games"]
    print(f"✅ Connected to MongoDB successfully. Database: {MONGODB_DB_NAME}")
except PyMongoError as e:
    print(f"❌ MongoDB Connection Error: {e}")
    raise SystemExit(
        "Application startup failed: Could not connect to MongoDB."
    )
# ---------------------------------

WORDS = [
    ("apple", "A crisp fruit that can be red or green", "Food", "easy"),
    ("beach", "A sandy place beside the sea", "Places", "easy"),
    ("cloud", "A white or grey shape floating in the sky", "Nature", "easy"),
    ("dream", "A story your mind creates while sleeping", "Life", "easy"),
    ("flame", "The bright, hot part of a fire", "Nature", "easy"),
    ("grape", "A small fruit that grows in bunches", "Food", "easy"),
    ("house", "A building where people live", "Places", "easy"),
    ("lemon", "A sour, yellow citrus fruit", "Food", "easy"),
    ("ocean", "A vast body of salt water", "Nature", "easy"),
    (
        "piano",
        "A musical instrument with black and white keys",
        "Music",
        "easy",
    ),
    (
        "planet",
        "A large world that moves around a star",
        "Science",
        "medium",
    ),
    (
        "bridge",
        "A structure that carries a path over an obstacle",
        "Places",
        "medium",
    ),
    ("camera", "A device used to capture photographs", "Objects", "medium"),
    ("forest", "A large area covered mainly with trees", "Nature", "medium"),
    ("guitar", "A stringed musical instrument", "Music", "medium"),
    ("island", "Land completely surrounded by water", "Places", "medium"),
    ("jungle", "A dense tropical forest", "Nature", "medium"),
    (
        "library",
        "A place where books are kept for reading",
        "Places",
        "medium",
    ),
    (
        "mystery",
        "Something difficult or impossible to explain",
        "Ideas",
        "medium",
    ),
    ("rainbow", "A colourful arc seen after rain", "Nature", "medium"),
    ("adventure", "An exciting or unusual experience", "Life", "hard"),
    ("butterfly", "An insect with large, colourful wings", "Animals", "hard"),
    ("chocolate", "A sweet food made from cocoa", "Food", "hard"),
    (
        "discovery",
        "The act of finding something for the first time",
        "Ideas",
        "hard",
    ),
    (
        "knowledge",
        "Information and understanding gained by learning",
        "Ideas",
        "hard",
    ),
    ("lightning", "A sudden electric flash in the sky", "Nature", "hard"),
    ("mountain", "A very high natural rise of land", "Nature", "hard"),
    (
        "orchestra",
        "A large group of musicians playing together",
        "Music",
        "hard",
    ),
    (
        "telescope",
        "An instrument used to view distant objects",
        "Science",
        "hard",
    ),
    (
        "umbrella",
        "An object held above the head to stop rain",
        "Objects",
        "hard",
    ),
]


def init_db():
    try:
        if words_collection.count_documents({}) == 0:
            docs = [
                {
                    "word": word,
                    "hint": hint,
                    "category": category,
                    "difficulty": difficulty,
                }
                for word, hint, category, difficulty in WORDS
            ]
            words_collection.insert_many(docs)
            print("🌱 Database initialized with default words.")
    except PyMongoError as e:
        print(f"⚠️ Error initializing database: {e}")


def masked_word(word, guessed):
    return [letter if letter in guessed else "" for letter in word]


def starter_letters(word, count=2):
    distinct_letters = list(dict.fromkeys(word))
    return random.sample(distinct_letters, min(count, len(distinct_letters)))


def game_payload(message="", status="playing"):
    game = session["game"]
    word = game["word"]
    guessed = game["guessed"]
    return {
        "masked": masked_word(word, guessed),
        "guessed": guessed,
        "wrongLetters": game["wrong_letters"],
        "attemptsLeft": game["attempts_left"],
        "maxAttempts": game["max_attempts"],
        "hint": game["hint"],
        "category": game["category"],
        "difficulty": game["difficulty"],
        "score": game["score"],
        "status": status,
        "message": message,
        "word": word if status != "playing" else None,
    }


def save_result(won):
    game = session["game"]
    try:
        games_collection.insert_one(
            {
                "player": session.get("player", "Explorer"),
                "word": game["word"],
                "difficulty": game["difficulty"],
                "won": won,
                "score": game["score"],
                "attempts": game["max_attempts"] - game["attempts_left"],
                "played_at": datetime.now(),
            }
        )
    except PyMongoError as e:
        print(f"⚠️ Failed to save game result to MongoDB: {e}")


@app.route("/")
def index():
    return render_template("index.html", player=session.get("player", ""))


@app.post("/api/start")
def start_game():
    data = request.get_json(silent=True) or {}
    player = str(data.get("player", "Explorer")).strip()[:24] or "Explorer"
    difficulty = data.get("difficulty", "medium")
    if difficulty not in {"easy", "medium", "hard"}:
        difficulty = "medium"

    try:
        choices = list(words_collection.find({"difficulty": difficulty}))
    except PyMongoError as e:
        return (
            jsonify({"error": "Database error fetching words.", "details": str(e)}),
            500,
        )

    if not choices:
        return jsonify({"error": "No words found for this difficulty."}), 500

    chosen = random.choice(choices)
    attempts = {"easy": 8, "medium": 7, "hard": 6}[difficulty]
    revealed_letters = starter_letters(chosen["word"])

    session["player"] = player
    session["game"] = {
        "word": chosen["word"],
        "hint": chosen["hint"],
        "category": chosen["category"],
        "difficulty": difficulty,
        "guessed": revealed_letters,
        "wrong_letters": [],
        "attempts_left": attempts,
        "max_attempts": attempts,
        "score": {"easy": 60, "medium": 90, "hard": 130}[difficulty],
        "finished": False,
    }
    return jsonify(
        game_payload(
            f"Your {difficulty} quest has begun with 2 letters revealed!"
        )
    )


@app.post("/api/guess")
def guess():
    if "game" not in session:
        return jsonify({"error": "Start a new game first."}), 400
    game = session["game"]
    if game["finished"]:
        return jsonify({"error": "This round is already finished."}), 400

    letter = str((request.get_json(silent=True) or {}).get("letter", "")).lower()
    if len(letter) != 1 or not letter.isalpha() or not letter.isascii():
        return jsonify({"error": "Choose one English letter."}), 400
    if letter in game["guessed"]:
        return jsonify(game_payload(f"You already tried “{letter.upper()}”."))

    game["guessed"].append(letter)
    message = "Great instinct! That letter is in the word."

    if letter not in game["word"]:
        game["wrong_letters"].append(letter)
        game["attempts_left"] -= 1
        game["score"] = max(0, game["score"] - 10)
        message = "Not this time—keep exploring!"

    status = "playing"
    if all(char in game["guessed"] for char in game["word"]):
        status = "won"
        game["finished"] = True
        message = f"Brilliant! You discovered {game['word'].upper()}."
        save_result(True)
    elif game["attempts_left"] == 0:
        status = "lost"
        game["finished"] = True
        message = f"Good try! The word was {game['word'].upper()}."
        save_result(False)

    session.modified = True
    return jsonify(game_payload(message, status))


@app.post("/api/reveal")
def reveal():
    if "game" not in session or session["game"]["finished"]:
        return jsonify({"error": "No active round."}), 400
    game = session["game"]
    hidden = [
        letter for letter in set(game["word"]) if letter not in game["guessed"]
    ]

    if not hidden or game["score"] < 15:
        return jsonify({"error": "Not enough points for a reveal."}), 400

    letter = random.choice(hidden)
    game["guessed"].append(letter)
    game["score"] -= 15

    status = "playing"
    message = f"Reveal unlocked: {letter.upper()} (−15 points)"

    if all(char in game["guessed"] for char in game["word"]):
        status = "won"
        game["finished"] = True
        message = f"Word discovered: {game['word'].upper()}!"
        save_result(True)

    session.modified = True
    return jsonify(game_payload(message, status))


@app.get("/api/stats")
def stats():
    player = session.get("player", "Explorer")
    try:
        games = list(games_collection.find({"player": player}))
        recent = list(
            games_collection.find({"player": player})
            .sort("played_at", -1)
            .limit(6)
        )
    except PyMongoError as e:
        return (
            jsonify({"error": "Database error fetching stats.", "details": str(e)}),
            500,
        )

    totals = {
        "games": len(games),
        "wins": sum(1 for g in games if g["won"]),
        "best_score": max((g["score"] for g in games), default=0),
        "total_score": sum(g["score"] for g in games),
    }

    for r in recent:
        r["_id"] = str(r["_id"])
        if isinstance(r["played_at"], datetime):
            r["played_at"] = r["played_at"].isoformat()

    return jsonify({**totals, "player": player, "recent": recent})


@app.get("/health")
def health():
    return {"status": "ok"}


init_db()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")