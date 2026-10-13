
import pandas as pd
import os
import joblib

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score
)

# 1. Load dataset
file_path = os.path.join(
    os.path.dirname(__file__),
    "..",
    "dataset",
    "fake_job_postings.csv.zip"
)

df = pd.read_csv(file_path)


# Dataset inspection
print("\n--- Dataset Overview ---")
print("Total rows and columns:", df.shape)

print("\nColumn names:")
print(df.columns.tolist())

print("\nMissing values:")
print(df.isnull().sum())

print("\nDuplicate rows:", df.duplicated().sum())

print("\nFake vs Genuine job counts:")
print(df["fraudulent"].value_counts())

print("\nFake vs Genuine percentages:")
print(
    (df["fraudulent"].value_counts(normalize=True) * 100)
    .round(2)
)


# 2. Select useful columns
text_columns = [
    "title",
    "company_profile",
    "description",
    "requirements",
    "benefits"
]

df[text_columns] = df[text_columns].fillna("")

# 3. Combine text
X = (
    df["title"].astype(str) + " " +
    df["company_profile"].astype(str) + " " +
    df["description"].astype(str) + " " +
    df["requirements"].astype(str) + " " +
    df["benefits"].astype(str)
)

y = df["fraudulent"]


# 4. Split data into train, validation and test sets

# First: 80% development data, 20% final test data
X_dev, X_test, y_dev, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

# Second: split the 80% development data
# into 75% training and 25% validation
X_train, X_val, y_train, y_val = train_test_split(
    X_dev,
    y_dev,
    test_size=0.25,
    random_state=42,
    stratify=y_dev
)

print("\n--- Data Split ---")
print("Training rows:", len(X_train))
print("Validation rows:", len(X_val))
print("Testing rows:", len(X_test))


# 5. Create ML pipeline
model = Pipeline([
    ("tfidf", TfidfVectorizer(
        stop_words="english",
        max_features=50000,
        ngram_range=(1, 2)
    )),
    ("classifier", LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        random_state=42
    ))
])


# 6. Train model
print("Training JobShield model...")
model.fit(X_train, y_train)

# 7. Compare thresholds on validation data
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

y_val_prob = model.predict_proba(X_val)[:, 1]

print("\n--- Validation Threshold Comparison ---")

for threshold in [0.50, 0.40, 0.30]:
    y_val_pred = (y_val_prob >= threshold).astype(int)

    print(f"\nThreshold: {threshold:.2f}")
    print("Accuracy:", round(
        accuracy_score(y_val, y_val_pred), 4
    ))

    print(classification_report(
        y_val,
        y_val_pred,
        target_names=["Genuine-labelled", "Fake-labelled"],
        zero_division=0
    ))

    print("Confusion Matrix:")
    print(confusion_matrix(y_val, y_val_pred))


# 8. Final evaluation on untouched test data
# Keep the selected baseline threshold at 0.50

chosen_threshold = 0.50

y_test_prob = model.predict_proba(X_test)[:, 1]
y_test_pred = (y_test_prob >= chosen_threshold).astype(int)

print("\n--- Final Test Results ---")
print("Selected threshold:", chosen_threshold)

print("\nClassification Report:")
print(classification_report(
    y_test,
    y_test_pred,
    target_names=["Genuine-labelled", "Fake-labelled"],
    zero_division=0
))

print("Confusion Matrix:")
print(confusion_matrix(y_test, y_test_pred))

print("Test Accuracy:", round(
    accuracy_score(y_test, y_test_pred), 4
))
