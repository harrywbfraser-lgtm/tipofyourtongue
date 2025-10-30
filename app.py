from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv
import openai
import os
import requests

# Load environment variables
load_dotenv()
app = Flask(__name__)

# Load OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
print("🔑 Loaded API key:", openai.api_key[:8] + "..." if openai.api_key else "❌ No API key found")

@app.route("/sitemap.xml")
def sitemap():
    return send_from_directory(".", "sitemap.xml")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/find_word", methods=["POST"])
def find_word():
    try:
        data = request.get_json(force=True)
        clue = data.get("clue", "").strip()
        
        if not clue:
            return jsonify({"error": "Please enter a clue."}), 400
        
        # ✅ Better prompt for structured output
        prompt = (
            f"Suggest up to 3 English words that fit this description: '{clue}'. "
            f"Return only the words, comma-separated (no explanations)."
        )
        
        # ✅ API call
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        
        # ✅ Parse the AI's text output
        raw_text = response.choices[0].message.content.strip()
        suggestions = [w.strip() for w in raw_text.split(",") if w.strip()]
        
        if not suggestions:
            return jsonify({"error": "No words found."}), 404
        
        primary_word = suggestions[0]
        alternatives = suggestions[1:]
        
        # ✅ Fetch definition (safe fallback)
        definition = "No definition found."
        try:
            dict_response = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{primary_word}")
            if dict_response.status_code == 200:
                dict_data = dict_response.json()  # ✅ FIXED: Different variable name
                if isinstance(dict_data, list) and "meanings" in dict_data[0]:
                    meaning = dict_data[0]["meanings"][0]
                    defs = meaning.get("definitions", [])
                    if defs:
                        definition = defs[0].get("definition", definition)
        except Exception as e:
            print("⚠️ Dictionary API error:", e)
        
        # ✅ Return clean structured JSON
        return jsonify({
            "primary": primary_word,
            "alternatives": alternatives,
            "definition": definition
        })
        
    except Exception as e:
        print("🔥 Flask error:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
