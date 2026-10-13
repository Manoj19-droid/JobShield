
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

url = "http://127.0.0.1:5000/api/analyze"

test_cases = [
    {
        "name": "Suspicious job",
        "job_text": (
            "Work from home job. "
            "Pay a registration fee of Rs. 1500."
        )
    },
    {
        "name": "Ordinary job description",
        "job_text": (
            "Software Engineer required. "
            "Candidates should know Python, SQL and Git. "
            "Responsibilities include developing and testing software."
        )
    },
    {
        "name": "Short job description",
        "job_text": "Hiring now. Apply today."
    }
]

for test in test_cases:
    print("\nTesting:", test["name"])

    data = {"job_text": test["job_text"]}

    request = Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urlopen(request, timeout=10) as response:
            result = response.read().decode("utf-8")
            print("HTTP status:", response.status)
            print("Backend response:", result)

    except HTTPError as error:
        print("HTTP error:", error.code)
        print(error.read().decode("utf-8"))

    except URLError as error:
        print("Connection error:", error.reason)

    except Exception as error:
        print("Unexpected error:", error)
