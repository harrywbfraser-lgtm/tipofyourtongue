from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import openai
import os
import requests
import csv
from datetime import datetime

# Load environment variables
load_dotenv()
app = Flask(__name__)

# OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
print("🔑 API key loaded:", "✅" if openai.api_key else "❌ MISSING")

# CSV log file path
LOG_FILE = "logs.csv"

# Ensure the log file has headers
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "clue", "suggested_word", "event_type"])


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/find_word", methods=["POST"])
def find_word():
    try:
        data = request.get_json(force=True)
        clue = data.get("clue", "").strip()
        previous = data.get("previous", [])
        is_retry = data.get("is_retry", False)

        if not clue:
            return jsonify({"error": "Please enter a clue."}), 400

        # Tell AI to avoid previously suggested words
        avoid_text = ""
        if previous:
            avoid_text = f" Avoid these words: {', '.join(previous)}."

        prompt = (
            f"Suggest up to 3 English words that fit this description: '{clue}'. "
            f"Only output the words, comma-separated. Do not repeat any of these words.{avoid_text}"
        )

        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = response.choices[0].message.content.strip()
        suggestions = [w.strip() for w in raw_text.split(",") if w.strip()]

        if not suggestions:
            return jsonify({"error": "No words found."}), 404

        primary_word = suggestions[0]
        alternatives = suggestions[1:]

        # Definition lookup
        definition = "No definition found."
        try:
            dict_response = requests.get(
                f"https://api.dictionaryapi.dev/api/v2/entries/en/{primary_word}"
            )
            if dict_response.status_code == 200:
                dict_data = dict_response.json()
                if isinstance(dict_data, list) and "meanings" in dict_data[0]:
                    meaning = dict_data[0]["meanings"][0]
                    defs = meaning.get("definitions", [])
                    if defs:
                        definition = defs[0].get("definition", definition)
        except Exception as e:
            print("⚠️ Dictionary API error:", e)

        # Log the suggestion or rejection
        event_type = "rejected" if is_retry else "suggested"
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [datetime.utcnow().isoformat(), clue, primary_word, event_type]
            )

        return jsonify(
            {"primary": primary_word, "alternatives": alternatives, "definition": definition}
        )

    except Exception as e:
        print("🔥 Flask error:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
