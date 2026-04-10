
#many languages with all features correctly working
import os
import re
import pandas as pd
from flask import Flask, request, render_template_string
from werkzeug.utils import secure_filename
from transformers import pipeline
from googletrans import Translator
from gtts import gTTS

# -----------------------------
# Config
# -----------------------------
UPLOAD_FOLDER = "uploads"
STATIC_FOLDER = "static"
ALLOWED_EXTENSIONS = {"txt", "csv"}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['STATIC_FOLDER'] = STATIC_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

# -----------------------------
# Load Models / Tools
# -----------------------------
print("Loading summarizer model...")
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
translator = Translator()
print("Models loaded!")

# -----------------------------
# Language List (full list from 3rd file)
# -----------------------------
LANGUAGES = {
    "none": "None (English only)",
    "af": "Afrikaans", "sq": "Albanian", "am": "Amharic", "ar": "Arabic",
    "hy": "Armenian", "az": "Azerbaijani", "eu": "Basque", "be": "Belarusian",
    "bn": "Bengali", "bs": "Bosnian", "bg": "Bulgarian", "ca": "Catalan",
    "ceb": "Cebuano", "zh": "Chinese (Simplified)", "zh-TW": "Chinese (Traditional)",
    "co": "Corsican", "hr": "Croatian", "cs": "Czech", "da": "Danish", "nl": "Dutch",
    "en": "English", "eo": "Esperanto", "et": "Estonian", "fi": "Finnish", "fr": "French",
    "fy": "Frisian", "gl": "Galician", "ka": "Georgian", "de": "German", "el": "Greek",
    "gu": "Gujarati", "ht": "Haitian Creole", "ha": "Hausa", "haw": "Hawaiian",
    "he": "Hebrew", "hi": "Hindi", "hmn": "Hmong", "hu": "Hungarian", "is": "Icelandic",
    "ig": "Igbo", "id": "Indonesian", "ga": "Irish", "it": "Italian", "ja": "Japanese",
    "jw": "Javanese", "kn": "Kannada", "kk": "Kazakh", "km": "Khmer", "ko": "Korean",
    "ku": "Kurdish", "ky": "Kyrgyz", "lo": "Lao", "la": "Latin", "lv": "Latvian",
    "lt": "Lithuanian", "lb": "Luxembourgish", "mk": "Macedonian", "mg": "Malagasy",
    "ms": "Malay", "ml": "Malayalam", "mt": "Maltese", "mi": "Maori", "mr": "Marathi",
    "mn": "Mongolian", "my": "Myanmar (Burmese)", "ne": "Nepali", "no": "Norwegian",
    "ny": "Nyanja (Chichewa)", "or": "Odia", "ps": "Pashto", "fa": "Persian", "pl": "Polish",
    "pt": "Portuguese", "pa": "Punjabi", "ro": "Romanian", "ru": "Russian", "sm": "Samoan",
    "gd": "Scots Gaelic", "sr": "Serbian", "st": "Sesotho", "sn": "Shona", "sd": "Sindhi",
    "si": "Sinhala", "sk": "Slovak", "sl": "Slovenian", "so": "Somali", "es": "Spanish",
    "su": "Sundanese", "sw": "Swahili", "sv": "Swedish", "tl": "Tagalog (Filipino)",
    "tg": "Tajik", "ta": "Tamil", "tt": "Tatar", "te": "Telugu", "th": "Thai",
    "tr": "Turkish", "tk": "Turkmen", "uk": "Ukrainian", "ur": "Urdu", "ug": "Uyghur",
    "uz": "Uzbek", "vi": "Vietnamese", "cy": "Welsh", "xh": "Xhosa", "yi": "Yiddish",
    "yo": "Yoruba", "zu": "Zulu"
}

# -----------------------------
# Helpers
# -----------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def summarize_text(text, chunk_size=900, max_length=150, min_length=50):
    words = text.split()
    chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
    summaries = []
    for chunk in chunks:
        try:
            summary = summarizer(chunk, max_length=max_length, min_length=min_length, do_sample=False)
            summaries.append(summary[0]['summary_text'])
        except Exception as e:
            summaries.append(f"[Error: {e}]")
    if len(summaries) > 1:
        combined_text = " ".join(summaries)
        return summarizer(combined_text, max_length=max_length, min_length=min_length, do_sample=False)[0]['summary_text']
    return summaries[0]

def detect_risks(summary):
    risks = []
    if re.search(r"terminate|breach|penalt|fine|liable", summary, re.I):
        risks.append("⚠️ Potential penalties or liabilities detected.")
    if re.search(r"dispute|arbitration|court", summary, re.I):
        risks.append("⚠️ Dispute resolution clauses found.")
    if re.search(r"confidential|non-disclosure", summary, re.I):
        risks.append("⚠️ Confidentiality obligations present.")
    if not risks:
        risks.append("✅ No major risks detected, but review with legal advisor if needed.")
    return risks + ["📌 Verify with legal authority.", "📌 Ask for clarifications.", "📌 Consult a lawyer if unsure."]

def detect_risks_from_csv(df):
    risks = []
    for _, row in df.iterrows():
        risk = str(row["risk_level"]).lower()
        clause_type = row["clause_type"]
        clause_text = str(row["clause_text"])[:120]
        if risk == "high":
            risks.append(f"⚠️ HIGH risk clause: {clause_type} → {clause_text}...")
        elif risk == "medium":
            risks.append(f"⚠️ Medium risk clause: {clause_type}")
        else:
            risks.append(f"✅ Low risk clause: {clause_type}")
    return risks

# -----------------------------
# HTML Template (styled + dropdown)
# -----------------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>LegalEase — Contract Summarizer</title>
  <style>
    body { font-family: Inter, sans-serif; background:#f5f7fb; margin:0; padding:20px;}
    .container { max-width: 900px; margin: 0 auto; background:white; border-radius:12px; 
                 box-shadow:0 6px 24px rgba(20,30,60,0.08); padding:24px;}
    h1 { font-size:24px; margin-bottom:10px; }
    input, select, button { margin:10px 0; padding:10px; font-size:14px; }
    button { background:#2563eb; color:white; border:none; border-radius:8px; cursor:pointer; }
    button:hover { background:#1e4ed8; }
    .section { margin-top:20px; }
    audio { margin-top:10px; display:block; }
    .card { background:#fcfcff; border-radius:10px; padding:12px; margin-bottom:10px; border:1px solid #eef2ff; }
    .muted { color:#64748b; font-size:13px; }
  </style>
</head>
<body>
  <div class="container">
    <h1>LegalEase — Contract Summarizer</h1>
    <p class="muted">Upload your legal document (.txt or .csv), get a summary, translation, audio, and risk guidance.</p>

    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="file" required><br>
        <label>Translate to:</label>
        <select name="language">
          {% for code, name in languages.items() %}
            <option value="{{ code }}">{{ name }}</option>
          {% endfor %}
        </select><br>
        <button type="submit">Proceed</button>
    </form>

    {% if summary %}
      <div class="section">
        <h3>English Summary:</h3>
        <div class="card">{{ summary }}</div>
        <audio controls><source src="{{ audio_en }}" type="audio/mpeg"></audio>
      </div>
    {% endif %}

    {% if translated %}
      <div class="section">
        <h3>Translated Summary:</h3>
        <div class="card">{{ translated }}</div>
        {% if audio_trans %}
          <audio controls><source src="{{ audio_trans }}" type="audio/mpeg"></audio>
        {% endif %}
      </div>
    {% endif %}

    {% if guidance %}
      <div class="section">
        <h3>Risk Analysis:</h3>
        <ul>
          {% for g in guidance %}
            <li>{{ g }}</li>
          {% endfor %}
        </ul>
      </div>
    {% endif %}
  </div>
</body>
</html>
"""

# -----------------------------
# Routes
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "": return "No file uploaded!"
        if not allowed_file(file.filename): return "Only .txt or .csv allowed!"

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        rows, content = None, ""
        try:
            if filename.endswith(".txt"):
                with open(filepath, "r", encoding="utf-8") as f: content = f.read()
            elif filename.endswith(".csv"):
                df = pd.read_csv(filepath)
                rows = df
                text_cols = df.select_dtypes(include=["object"]).columns
                content = " ".join(df[text_cols].astype(str).agg(" ".join, axis=1))
        except Exception as e: return f"Error reading file: {e}"

        try:
            english_summary = summarize_text(content)
        except Exception as e: return f"Summarization failed: {e}"

        target_lang = request.form.get("language")
        translated_summary = None
        if target_lang and target_lang != "none":
            try: translated_summary = translator.translate(english_summary, dest=target_lang).text
            except Exception as e: translated_summary = f"Translation failed: {e}"

        try:
            tts_path_en = os.path.join(app.config["STATIC_FOLDER"], "summary_en.mp3")
            gTTS(english_summary).save(tts_path_en)
            tts_path_trans = None
            if translated_summary and not translated_summary.startswith("Translation failed"):
                tts_path_trans = os.path.join(app.config["STATIC_FOLDER"], "summary_trans.mp3")
                gTTS(translated_summary, lang=target_lang).save(tts_path_trans)
        except Exception as e: return f"TTS failed: {e}"

        guidance = detect_risks_from_csv(rows) if rows is not None else detect_risks(english_summary)

        return render_template_string(HTML_TEMPLATE,
            summary=english_summary, translated=translated_summary,
            audio_en="/static/summary_en.mp3",
            audio_trans="/static/summary_trans.mp3" if translated_summary else None,
            guidance=guidance, languages=LANGUAGES)

    return render_template_string(HTML_TEMPLATE, languages=LANGUAGES)

if __name__ == "__main__":
    app.run(debug=True)



