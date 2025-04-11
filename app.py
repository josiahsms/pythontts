# app.py (main Flask application)

from flask import Flask, render_template, request, jsonify
import requests
import os
import redis
import json

app = Flask(__name__)

# ElevenLabs API Key and Voice ID (replace with your actual values)
ELEVEN_LABS_API_KEY = os.environ.get("ELEVEN_LABS_API_KEY")
ELEVEN_LABS_VOICE_ID = os.environ.get("ELEVEN_LABS_VOICE_ID")

# Upstash Redis connection (replace with your Upstash Redis URL)
UPSTASH_REDIS_URL = os.environ.get("UPSTASH_REDIS_URL")
r = redis.from_url(UPSTASH_REDIS_URL)

@app.route("/", methods=["GET", "POST"])
def index():
    audio_url = None
    if request.method == "POST":
        text = request.form.get("text")
        pronunciation_text = request.form.get("pronunciation_text")
        pronunciation_phonetic = request.form.get("pronunciation_phonetic")

        if text:
            # Apply custom pronunciations
            pronunciations = r.get("pronunciations")
            if pronunciations:
                pronunciations = json.loads(pronunciations)
                for word, phonetic in pronunciations.items():
                    text = text.replace(word, phonetic)

            audio_url = generate_speech(text)

        if pronunciation_text and pronunciation_phonetic:
            # Store pronunciation in Redis
            pronunciations = r.get("pronunciations")
            if pronunciations:
                pronunciations = json.loads(pronunciations)
            else:
                pronunciations = {}
            pronunciations[pronunciation_text] = pronunciation_phonetic
            r.set("pronunciations", json.dumps(pronunciations))
    return render_template("index.html", audio_url=audio_url)

def generate_speech(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_LABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVEN_LABS_API_KEY,
        "Content-Type": "application/json",
        "accept": "audio/mpeg"
    }
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        # Save the audio to a file or return a URL. For simplicity, let's save to a temp file.
        temp_filename = "temp_audio.mp3"
        with open(temp_filename, "wb") as f:
            f.write(response.content)
        #For production, it is highly recommended to store the audio in a cloud storage and return the URL.
        return f"/{temp_filename}" #This is for local testing. In production you would return a cloud storage url.

    else:
        print(f"ElevenLabs API Error: {response.status_code}, {response.text}")
        return None

if __name__ == "__main__":
    app.run(debug=True) # Set debug to false in production.
