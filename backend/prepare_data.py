
import pandas as pd
import os

file_path = os.path.join(
    os.path.dirname(__file__),
    "..",
    "dataset",
    "fake_job_postings.csv.zip"
)

df = pd.read_csv(file_path)

print("Missing values in important columns:")

columns = [
    "title",
    "company_profile",
    "description",
    "requirements",
    "fraudulent"
]

print(df[columns].isnull().sum())

print("\nJob label distribution:")
print(df["fraudulent"].value_counts())
