
import os
import re
import ipaddress
import socket
import joblib
import requests

from bs4 import BeautifulSoup
from urllib.parse import urlparse
from flask import Flask, request, jsonify
from flask_cors import CORS


# ==========================================
# 1. FLASK APP SETUP
# ==========================================

app = Flask(__name__)
CORS(app)

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "jobshield_model.pkl"
)

model = joblib.load(MODEL_PATH)


# ==========================================
# 2. WARNING SIGN DETECTION
# ==========================================

def find_warning_signs(job_text):
    text = (job_text or "").lower()

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


# ==========================================
# 3. BASIC URL VALIDATION
# ==========================================

def check_url_basics(url):
    findings = []
    url = (url or "").strip()

    if not url:
        return {
            "valid": False,
            "normalized_url": None,
            "findings": ["Please provide a URL."]
        }

    if "://" not in url:
        url = "https://" + url

    try:
        parsed = urlparse(url)
        hostname = parsed.hostname

        if parsed.scheme not in ("http", "https"):
            raise ValueError("Unsupported URL scheme")

        if not hostname or "." not in hostname:
            raise ValueError("Invalid hostname")

        if parsed.username is not None or parsed.password is not None:
            raise ValueError("Embedded credentials are not allowed")

        # Validate malformed port values
        _ = parsed.port

    except (ValueError, UnicodeError):
        return {
            "valid": False,
            "normalized_url": None,
            "findings": [
                "The URL format is invalid or unsupported."
            ]
        }

    hostname = hostname.lower()

    if (
        hostname in {"localhost", "localhost.localdomain"}
        or hostname.endswith(".local")
    ):
        return {
            "valid": False,
            "normalized_url": None,
            "findings": [
                "Local website addresses are not allowed."
            ]
        }

    if parsed.scheme != "https":
        findings.append("The URL does not use HTTPS.")

    # Reject private and non-public IP addresses
    try:
        ip = ipaddress.ip_address(hostname)

        if not ip.is_global:
            return {
                "valid": False,
                "normalized_url": None,
                "findings": [
                    "Private or non-public IP addresses are not allowed."
                ]
            }

        # IP-based URLs are not fetched by this project
        return {
            "valid": False,
            "normalized_url": None,
            "findings": [
                "IP-based URLs are not supported. Use a public domain name."
            ]
        }

    except ValueError:
        # Hostname is not an IP address
        pass

    # Check for punycode domain labels
    domain_labels = hostname.split(".")

    if any(label.startswith("xn--") for label in domain_labels):
        findings.append(
            "The domain contains a punycode label; verify it carefully."
        )

    if len(url) > 2048:
        return {
            "valid": False,
            "normalized_url": None,
            "findings": ["The URL is unusually long."]
        }

    # Basic DNS check to reject hostnames resolving to non-public IPs.
    # This is a precaution, not a complete security guarantee.
    try:
        addresses = socket.getaddrinfo(
            hostname,
            parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM
        )

        if not addresses:
            raise ValueError("No DNS addresses found")

        for address in addresses:
            resolved_ip = ipaddress.ip_address(address[4][0])

            if not resolved_ip.is_global:
                return {
                    "valid": False,
                    "normalized_url": None,
                    "findings": [
                        "The domain resolves to a non-public IP address."
                    ]
                }

    except (socket.gaierror, ValueError, OSError):
        return {
            "valid": False,
            "normalized_url": None,
            "findings": [
                "The domain could not be validated as a public website."
            ]
        }

    return {
        "valid": True,
        "normalized_url": url,
        "findings": findings
    }


# ==========================================
# 4. EXTRACT TEXT FROM A JOB WEBPAGE
# ==========================================

def read_job_webpage(url):
    url_check = check_url_basics(url)

    if not url_check["valid"]:
        return {
            "success": False,
            "message": "URL validation failed: "
                       + " ".join(url_check["findings"]),
            "job_text": "",
            "title": ""
        }

    safe_url = url_check["normalized_url"]

    try:
        response = requests.get(
            safe_url,
            timeout=10,
            allow_redirects=False,
            headers={
                "User-Agent": "JobShield/1.0"
            },
            stream=True
        )

        if response.is_redirect or response.is_permanent_redirect:
            response.close()

            return {
                "success": False,
                "message": (
                    "This webpage redirects to another URL. "
                    "Redirects are not followed in this version."
                ),
                "job_text": "",
                "title": ""
            }

        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type", ""
        ).lower()

        if "text/html" not in content_type:
            response.close()

            return {
                "success": False,
                "message": "The URL did not return an HTML webpage.",
                "job_text": "",
                "title": ""
            }

        max_bytes = 1_000_000
        content = bytearray()

        for chunk in response.iter_content(chunk_size=8192):
            content.extend(chunk)

            if len(content) > max_bytes:
                response.close()

                return {
                    "success": False,
                    "message": "The webpage is too large to process.",
                    "job_text": "",
                    "title": ""
                }

        response.close()

        html_text = bytes(content).decode(
            "utf-8",
            errors="replace"
        )

        soup = BeautifulSoup(html_text, "html.parser")

        # Remove elements that usually do not contain job details
        for element in soup([
            "script",
            "style",
            "noscript",
            "svg",
            "iframe",
            "nav",
            "footer"
        ]):
            element.decompose()

        title = (
            soup.title.get_text(" ", strip=True)
            if soup.title else ""
        )

        main = (
            soup.find("main")
            or soup.find("article")
            or soup.body
        )

        if main is None:
            return {
                "success": False,
                "message": "No readable webpage content was found.",
                "job_text": "",
                "title": title
            }

        job_text = main.get_text(" ", strip=True)
        job_text = re.sub(r"\s+", " ", job_text).strip()

        if len(job_text) < 100:
            return {
                "success": False,
                "message": (
                    "Very little text was found. "
                    "The webpage may require JavaScript or login."
                ),
                "job_text": job_text,
                "title": title
            }

        return {
            "success": True,
            "message": "Webpage text extracted successfully.",
            "job_text": job_text[:20000],
            "title": title
        }

    except requests.RequestException:
        return {
            "success": False,
            "message": (
                "Could not read the webpage. "
                "The site may block automated requests "
                "or may be unavailable."
            ),
            "job_text": "",
            "title": ""
        }


# ==========================================
# 5. SHARED JOB ANALYSIS FUNCTION
# ==========================================

def analyze_job_data(data):
    url = str(data.get("url", "") or "").strip()

    fields = [
        "title",
        "company_profile",
        "description",
        "requirements"
    ]

    pasted_text = " ".join(
        str(data.get(field, "") or "")
        for field in fields
    ).strip()

    # Support the existing frontend format
    if not pasted_text:
        pasted_text = str(
            data.get("job_text", "") or ""
        ).strip()

    page_title = ""
    extracted_text = ""
    source_note = ""

    # If URL is provided, try to extract its text
    if url:
        page = read_job_webpage(url)

        if page["success"]:
            page_title = page.get("title", "")
            extracted_text = page.get("job_text", "")

        elif pasted_text:
            # If webpage extraction fails, use pasted description
            source_note = (
                "The webpage could not be read. "
                "Analysis uses the description you provided."
            )

        else:
            return {
                "message": page["message"],
                "page_title": page.get("title", ""),
                "prediction": "Unable to Analyze",
                "label": None,
                "fake_probability": None,
                "risk_score": None,
                "warning_signs": [],
                "review_recommended": True,
                "note": (
                    "Please paste the job description if "
                    "the webpage cannot be read."
                )
            }, 422

    # Combine all available sources
    combined_parts = []

    if page_title:
        combined_parts.append(page_title)

    if extracted_text:
        combined_parts.append(extracted_text)

    if pasted_text:
        combined_parts.append(pasted_text)

    job_text = " ".join(combined_parts).strip()

    if not job_text:
        return {
            "message": "Please provide a job URL or description."
        }, 400

    warning_signs = find_warning_signs(job_text)

    # Guard against extremely short descriptions
    if len(job_text.split()) < 10:
        return {
            "message": "Insufficient information",
            "prediction": "Insufficient Information",
            "label": None,
            "fake_probability": None,
            "risk_score": None,
            "warning_signs": warning_signs,
            "review_recommended": True,
            "page_title": page_title,
            "extracted_text_length": len(extracted_text),
            "note": (
                "The available job text is too short to make "
                "a reliable prediction. Please provide more details."
            )
        }, 200

    try:
        prediction = int(model.predict([job_text])[0])

        probabilities = model.predict_proba([job_text])[0]
        fake_index = list(model.classes_).index(1)

        fake_probability = float(
            probabilities[fake_index]
        ) * 100

    except (ValueError, IndexError):
        return {
            "message": "Could not analyze the provided job text."
        }, 500

    note = (
        "This is a model estimate, not proof of fraud. "
        "Verify the employer independently."
    )

    if source_note:
        note = source_note + " " + note

    return {
        "message": "Job analysis complete.",
        "page_title": page_title,
        "prediction": "Fake" if prediction == 1 else "Genuine",
        "label": prediction,
        "fake_probability": round(fake_probability, 2),
        "risk_score": round(fake_probability),
        "warning_signs": warning_signs,
        "review_recommended": len(warning_signs) > 0,
        "extracted_text_length": len(extracted_text),
        "note": note
    }, 200


# ==========================================
# 6. HOME ROUTE
# ==========================================

@app.route("/")
def home():
    return "JobShield backend is running!"


# ==========================================
# 7. ANALYZE DESCRIPTION, URL OR BOTH
# ==========================================

@app.route("/api/analyze", methods=["POST"])
def analyze_job():
    data = request.get_json(silent=True) or {}

    result, status_code = analyze_job_data(data)

    return jsonify(result), status_code


# ==========================================
# 8. URL-ONLY ENDPOINT
# ==========================================

@app.route("/api/analyze-url", methods=["POST"])
def analyze_job_url():
    data = request.get_json(silent=True) or {}

    url = str(data.get("url", "") or "").strip()

    if not url:
        return jsonify({
            "message": "Please provide a job posting URL."
        }), 400

    result, status_code = analyze_job_data({
        "url": url
    })

    return jsonify(result), status_code


# ==========================================
# 9. BASIC URL CHECKER ENDPOINT
# ==========================================

@app.route("/api/check-url", methods=["POST"])
def check_url():
    data = request.get_json(silent=True) or {}

    url = str(data.get("url", "") or "")

    result = check_url_basics(url)

    if not result["valid"]:
        return jsonify({
            "message": "URL check could not be completed.",
            **result,
            "threat_intelligence": {
                "status": "not_checked"
            }
        }), 400

    return jsonify({
        "message": "Basic URL check complete.",
        **result,
        "threat_intelligence": {
            "status": "not_configured",
            "note": (
                "Threat-intelligence lookup has not "
                "been connected yet."
            )
        },
        "note": (
            "Basic URL checks cannot prove that a website "
            "is safe or fraudulent."
        )
    })


# ==========================================
# 10. START FLASK SERVER
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)
