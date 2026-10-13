
import os
import joblib
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "jobshield_model.pkl"
)

model = joblib.load(MODEL_PATH)


def find_warning_signs(job_text):
    text = job_text.lower()

    warning_rules = {
        "Requests a registration fee or payment": [
            "registration fee",
            "pay money",
            "security deposit",
            "processing fee",
            "pay a fee",
            "training fee",
            "advance payment",
            "joining fee",
            "job fee",
            "interview fee",
            "refundable deposit",
            "pay to get hired",
            "transfer a joining deposit",
            "pay before joining",
            "payment to confirm your job"
        ],

        "Promises unusually high or guaranteed earnings": [
            "guaranteed income",
            "earn money instantly",
            "get rich quickly",
            "earn without working",
            "make thousands daily",
            "earn rs. 80000",
            "earn rs 80000",
            "earn 80000"
        ],

        "Claims suspicious or instant selection": [
            "no interview",
            "without interview",
            "direct joining",
            "selected without interview",
            "guaranteed selection",
            "instant job offer"
        ],

        "Uses urgency or pressure tactics": [
            "apply immediately",
            "limited vacancies",
            "act now",
            "urgent hiring",
            "today only",
            "offer expires today",
            "last chance to apply",
            "immediate payment required"
        ],

        "Requests sensitive information": [
            "share your otp",
            "send your otp",
            "share your password",
            "bank account password",
            "send your cvv",
            "share your cvv",
            "send your banking details"
        ],

        "Uses potentially suspicious communication or payment methods": [
            "contact only on whatsapp",
            "message only on telegram",
            "no company website",
            "pay through gift card",
            "send cryptocurrency"
        ]
    }

    found_signs = []

    for reason, phrases in warning_rules.items():
        if any(phrase in text for phrase in phrases):
            found_signs.append(reason)

    return found_signs




@app.route("/")
def home():
    return "JobShield backend is running!"


@app.route("/api/analyze", methods=["POST"])
def analyze_job():
    data = request.get_json(silent=True) or {}

    fields = [
        "title",
        "company_profile",
        "description",
        "requirements"
    ]

    job_text = " ".join(
        str(data.get(field, "") or "")
        for field in fields
    ).strip()

    # Purane frontend/test ke format ko bhi support karega
    if not job_text:
        job_text = str(data.get("job_text", "") or "").strip()

    if not job_text:
        return jsonify({
            "message": "Please enter a job description."
        }), 400

    prediction = int(model.predict([job_text])[0])
    
    warning_signs = find_warning_signs(job_text)
 

    probabilities = model.predict_proba([job_text])[0]

    fake_index = list(model.classes_).index(1)
    fake_probability = float(probabilities[fake_index]) * 100

    return jsonify({
        "message": "Analysis complete",
        "prediction": "Fake" if prediction == 1 else "Genuine",
        "label": prediction,
        "fake_probability": round(fake_probability, 2),
        "risk_score": round(fake_probability),
        
        "warning_signs": warning_signs,
        "note": "This is a model estimate, not proof of fraud."
    })


if __name__ == "__main__":
    app.run(debug=True)
