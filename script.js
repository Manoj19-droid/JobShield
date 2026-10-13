
const jobText = document.getElementById("jobText");
const jobUrlInput = document.getElementById("jobUrl");
const highlightLayer = document.getElementById("highlightLayer");

const checkBtn = document.getElementById("checkBtn");
const sampleBtn = document.getElementById("sampleBtn");
const clearBtn = document.getElementById("clearBtn");

const buttonText = document.getElementById("buttonText");
const loader = document.getElementById("loader");

const resultBox = document.getElementById("resultBox");
const resultText = document.getElementById("resultText");
const reasonText = document.getElementById("reasonText");
const riskLabel = document.getElementById("riskLabel");
const riskBar = document.getElementById("riskBar");
const signsList = document.getElementById("signsList");
const confidenceText = document.getElementById("confidenceText");

// Flask backend URL
const API_BASE = "http://127.0.0.1:5000";
const ANALYZE_TEXT_URL = `${API_BASE}/api/analyze`;
const ANALYZE_JOB_URL = `${API_BASE}/api/analyze-url`;

const sampleJob = `Congratulations! You have been selected for a work from home job.
Earn Rs. 80000 per month without any experience.
Pay a registration fee of Rs. 1500 today to confirm your job.
No interview required. Limited vacancies available!`;

const suspiciousPhrases = [
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
    "payment to confirm your job",
    "guaranteed income",
    "earn money instantly",
    "get rich quickly",
    "earn without working",
    "no experience needed",
    "earn rs. 80000",
    "earn rs 80000",
    "earn 80000",
    "make thousands daily",
    "no interview",
    "without interview",
    "direct joining",
    "selected without interview",
    "guaranteed selection",
    "instant job offer",
    "apply immediately",
    "limited vacancies",
    "act now",
    "urgent hiring",
    "today only",
    "offer expires today",
    "last chance to apply",
    "immediate payment required",
    "share your otp",
    "send your otp",
    "share your password",
    "bank account password",
    "send your cvv",
    "share your cvv",
    "send your banking details",
    "contact only on whatsapp",
    "message only on telegram",
    "no company website",
    "pay through gift card",
    "send cryptocurrency"
];

const warningChecks = [
    {
        name: "Registration fee or payment requested",
        icon: "💳",
        level: "High concern",
        keywords: [
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
        ]
    },
    {
        name: "Unusually high or guaranteed earnings",
        icon: "💰",
        level: "Review carefully",
        keywords: [
            "guaranteed income",
            "earn money instantly",
            "get rich quickly",
            "earn without working",
            "make thousands daily",
            "earn rs. 80000",
            "earn rs 80000",
            "earn 80000"
        ]
    },
    {
        name: "Claims suspicious or instant selection",
        icon: "📋",
        level: "Review carefully",
        keywords: [
            "no interview",
            "without interview",
            "direct joining",
            "selected without interview",
            "guaranteed selection",
            "instant job offer"
        ]
    },
    {
        name: "Uses urgency or pressure tactics",
        icon: "⏰",
        level: "Review carefully",
        keywords: [
            "apply immediately",
            "limited vacancies",
            "act now",
            "urgent hiring",
            "today only",
            "offer expires today",
            "last chance to apply",
            "immediate payment required"
        ]
    },
    {
        name: "Requests sensitive information",
        icon: "🔐",
        level: "High concern",
        keywords: [
            "share your otp",
            "send your otp",
            "share your password",
            "bank account password",
            "send your cvv",
            "share your cvv",
            "send your banking details"
        ]
    },
    {
        name: "Potentially suspicious communication or payment method",
        icon: "📱",
        level: "Review carefully",
        keywords: [
            "contact only on whatsapp",
            "message only on telegram",
            "no company website",
            "pay through gift card",
            "send cryptocurrency"
        ]
    }
];

// HTML special characters ko safe banata hai
function escapeHTML(text) {
    return text.replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[character]);
}

// Regex mein special characters ko safely handle karta hai
function escapeRegExp(text) {
    return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// Suspicious phrases ko textarea ke peeche highlight karta hai
function updateHighlight() {
    if (!highlightLayer || !jobText) return;

    const originalText = jobText.value;
    let safeText = escapeHTML(originalText);

    const phrases = [...suspiciousPhrases].sort(
        (a, b) => b.length - a.length
    );

    const pattern = phrases.map(escapeRegExp).join("|");

    if (pattern && originalText.length > 0) {
        const regex = new RegExp(pattern, "gi");

        safeText = safeText.replace(
            regex,
            match => `<mark>${match}</mark>`
        );
    }

    highlightLayer.innerHTML = safeText + "\n";
    syncScroll();
}

// Textarea aur highlight layer ka scroll sync karta hai
function syncScroll() {
    if (!jobText || !highlightLayer) return;

    highlightLayer.scrollTop = jobText.scrollTop;
    highlightLayer.scrollLeft = jobText.scrollLeft;
}

jobText.addEventListener("input", updateHighlight);
jobText.addEventListener("scroll", syncScroll);

// Loading state
function showLoading(isLoading) {
    checkBtn.disabled = isLoading;
    sampleBtn.disabled = isLoading;
    clearBtn.disabled = isLoading;

    buttonText.innerText = isLoading
        ? "Analyzing..."
        : "🔎 Analyze Job";

    checkBtn.classList.toggle("loading", isLoading);
    loader.style.display = isLoading ? "inline-block" : "none";
}

// Result section ko initial state mein laata hai
function resetResult() {
    resultBox.className = "result";

    resultBox.querySelector(".result-icon").innerText = "🤖";

    resultText.innerText = "Your result will appear here";

    reasonText.innerText =
        "Paste a job posting and select Analyze Job.";

    riskLabel.innerText = "Not analyzed";
    riskBar.style.width = "0%";
    riskBar.className = "risk-bar";

    signsList.innerHTML =
        '<li class="neutral-sign">Analysis has not started yet.</li>';

    confidenceText.innerText = "";
}

// Input clear karta hai
function clearAll() {
    jobText.value = "";
    jobUrlInput.value = "";

    updateHighlight();
    resetResult();
    showLoading(false);

    jobText.focus();
}

// Sample suspicious job fill karta hai
sampleBtn.addEventListener("click", function () {
    jobUrlInput.value = "";
    jobText.value = sampleJob;

    updateHighlight();
    resetResult();

    jobText.focus();
});

clearBtn.addEventListener("click", clearAll);

// Main Analyze Job button
checkBtn.addEventListener("click", async function () {
    const job = jobText.value.trim();
    const jobUrl = jobUrlInput.value.trim();

    if (!job && !jobUrl) {
        resetResult();

        resultText.innerText = "Please enter a job posting";

        reasonText.innerText =
            "Paste a job description or enter a job application link.";

        return;
    }

    // URL diya hai toh URL endpoint use hoga
    
     const endpoint = ANALYZE_TEXT_URL;

    const payload = {
    url: jobUrl,
    job_text: job
     };


    showLoading(true);

    resultBox.className = "result";

    resultText.innerText = "Analyzing job posting...";

    reasonText.innerText =
        "Sending details to the JobShield analysis system.";

    riskLabel.innerText = "Analyzing...";
    riskBar.style.width = "0%";
    riskBar.className = "risk-bar";

    signsList.innerHTML =
        '<li class="neutral-sign">Checking for warning signs...</li>';

    confidenceText.innerText = "";

    try {
        const response = await fetch(endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.message ||
                "The server could not analyze this job."
            );
        }

        // Text analysis mein entered job text available hai.
        // URL endpoint extracted text return nahi karta,
        // isliye URL ke liye backend warning signs use honge.
        const analyzedText = job;

        displayMLResult(data, analyzedText);

    } catch (error) {
        resultBox.className = "result";

        resultBox.querySelector(".result-icon").innerText = "⚠️";

        resultText.innerText = "Analysis failed";

        reasonText.innerText =
            "Could not analyze the job. Check that Flask is running and try again.";

        riskLabel.innerText = "Unavailable";
        riskBar.style.width = "0%";
        riskBar.className = "risk-bar";

        signsList.innerHTML =
            '<li class="neutral-sign">Analysis could not be completed.</li>';

        confidenceText.innerText =
            error.message || "Unknown error.";

    } finally {
        showLoading(false);
    }
});

// API se aaye result ko screen par dikhata hai
function displayMLResult(data, job) {
    const prediction = data.prediction;

    const hasScore =
        data.risk_score !== null &&
        data.risk_score !== undefined &&
        Number.isFinite(Number(data.risk_score));

    const score = hasScore
        ? Number(data.risk_score)
        : null;

    const hasProbability =
        data.fake_probability !== null &&
        data.fake_probability !== undefined &&
        Number.isFinite(Number(data.fake_probability));

    const probability = hasProbability
        ? Number(data.fake_probability)
        : null;

    showWarningSigns(job, data.warning_signs);

    // Short description ke liye Fake/Genuine claim nahi karna
    if (
        prediction === "Insufficient Information" ||
        data.label === null ||
        data.message === "Insufficient information"
    ) {
        resultBox.className = "result medium";

        resultBox.querySelector(".result-icon").innerText = "📝";

        resultText.innerText = "Insufficient Information";

        reasonText.innerText =
            data.note ||
            "Please provide a more complete job description before relying on a prediction.";

        riskLabel.innerText = "Not available";
        riskBar.style.width = "0%";
        riskBar.className = "risk-bar";

        confidenceText.innerText =
            "No reliable Fake/Genuine prediction was made for this short description.";

        return;
    }

    const isFake = prediction === "Fake";
    const reviewRecommended = data.review_recommended === true;

    let level = "Low";

    if (score !== null) {
        if (score >= 70) {
            level = "High";
        } else if (score >= 40) {
            level = "Medium";
        }
    }

    // Warning signs hone par result ko green "safe" style mat do
    resultBox.className = "result " + (
        isFake
            ? "fake"
            : reviewRecommended
                ? "medium"
                : "genuine"
    );

    resultBox.querySelector(".result-icon").innerText =
        isFake
            ? "🚨"
            : reviewRecommended
                ? "⚠️"
                : "🤖";

    resultText.innerText = isFake
        ? "ML Prediction: Potentially Fake"
        : "ML Prediction: Genuine-labelled";

    if (reviewRecommended) {
        reasonText.innerText =
            "Warning signs were detected. Do not pay fees or share sensitive information. Verify the employer independently; the model's label is not a safety guarantee.";
    } else {
        reasonText.innerText = isFake
            ? "The model classified this job as potentially fraudulent. Verify the employer independently before proceeding."
            : "No listed warning signs were detected, but this does not guarantee the job is legitimate. Verify the employer independently.";
    }

    if (score === null) {
        riskLabel.innerText = "Not available";
        riskBar.style.width = "0%";
        riskBar.className = "risk-bar";
    } else {
        riskLabel.innerText =
            `${level} Estimated Risk (${score}/100)`;

        riskBar.style.width =
            `${Math.max(0, Math.min(100, score))}%`;

        riskBar.className =
            `risk-bar ${level.toLowerCase()}`;
    }

    if (probability === null) {
        confidenceText.innerText =
            data.note ||
            "A model probability is not available for this result.";
    } else {
        confidenceText.innerText =
            `Model-estimated fake probability: ${probability.toFixed(2)}%. ` +
            (data.note || "This estimate is not proof of fraud.");
    }
}

// Warning signs ki list banata hai
function showWarningSigns(job, backendWarningSigns) {
    const text = (job || "").toLowerCase();

    signsList.innerHTML = "";

    let foundCount = 0;

    warningChecks.forEach(function (check) {
        const matchedPhrases = check.keywords.filter(
            phrase => text.includes(phrase)
        );

        if (matchedPhrases.length === 0) return;

        foundCount++;

        const item = document.createElement("li");
        item.className = "warning-card";

        const heading = document.createElement("div");
        heading.className = "warning-card-title";
        heading.innerText = `${check.icon} ${check.name}`;

        const badge = document.createElement("span");
        badge.className = "warning-level";
        badge.innerText = check.level;

        const evidenceLabel = document.createElement("div");
        evidenceLabel.className = "evidence-label";
        evidenceLabel.innerText = "Matched evidence";

        const evidence = document.createElement("div");
        evidence.className = "evidence-text";

        const originalPhrases = matchedPhrases.map(function (phrase) {
            const index = text.indexOf(phrase);

            return job.substring(
                index,
                index + phrase.length
            );
        });

        evidence.innerText = originalPhrases
            .map(phrase => `"${phrase}"`)
            .join(", ");

        item.append(
            heading,
            badge,
            evidenceLabel,
            evidence
        );

        signsList.appendChild(item);
    });

    // URL analysis mein backend warning categories fallback hain
    if (
        Array.isArray(backendWarningSigns) &&
        backendWarningSigns.length > 0
    ) {
        backendWarningSigns.forEach(function (reason) {
            const alreadyShown = warningChecks.some(check =>
                check.name === reason ||
                (
                    reason === "Requests a registration fee or payment" &&
                    check.name === "Registration fee or payment requested"
                )
            );

            if (alreadyShown && foundCount > 0) return;

            const item = document.createElement("li");
            item.className = "warning-card";
            item.innerText = `⚠️ ${reason}`;

            signsList.appendChild(item);
            foundCount++;
        });
    }

    if (foundCount === 0) {
        const item = document.createElement("li");
        item.className = "neutral-sign";

        item.innerText =
            "No listed warning phrases detected. This does not guarantee the job is safe.";

        signsList.appendChild(item);
    }
}

// Page load hone par initial state set karo
updateHighlight();
resetResult();

/* ===== JobShield Welcome Voice ===== */

document.addEventListener("DOMContentLoaded", () => {
    const hero = document.getElementById("welcomeHero");
    const speechBubble = document.querySelector(".speech-bubble");

    if (!hero || !speechBubble) return;

    const message = "Hey! We are here for your help.";

    // Create a visual mouth effect on the character image area.
    const character = document.querySelector(".welcome-character");

    if (character && !document.querySelector(".speaking-indicator")) {
        const indicator = document.createElement("span");
        indicator.className = "speaking-indicator";
        indicator.setAttribute("aria-hidden", "true");
        character.appendChild(indicator);
    }

    // Browsers may block automatic speech until the user interacts.
    // So show a Speak button instead of forcing audio on page load.
    const speakButton = document.createElement("button");
    speakButton.type = "button";
    speakButton.textContent = "🔊 Hear our welcome";
    speakButton.className = "welcome-speak-button";
    speechBubble.appendChild(speakButton);

    speakButton.addEventListener("click", () => {
        if (!("speechSynthesis" in window)) {
            speakButton.textContent = "Voice is not supported in this browser";
            return;
        }

        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(message);
        utterance.lang = "en-US";
        utterance.rate = 0.9;
        utterance.pitch = 1.05;

        utterance.onstart = () => {
            hero.classList.add("is-speaking");
            speakButton.textContent = "🔊 Speaking...";
        };

        utterance.onend = () => {
            hero.classList.remove("is-speaking");
            speakButton.textContent = "🔊 Hear our welcome";
        };

        utterance.onerror = () => {
            hero.classList.remove("is-speaking");
            speakButton.textContent = "🔊 Try speaking again";
        };

        window.speechSynthesis.speak(utterance);
    });
});

