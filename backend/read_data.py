
import pandas as pd
import os

file_path = os.path.join(
    os.path.dirname(__file__),
    "..",
    "dataset",
    "fake_job_postings.csv.zip"
)

df = pd.read_csv(file_path)

print("Dataset loaded successfully!")
print("\nFirst 5 rows:")
print(df.head())

print("\nDataset shape:")
print(df.shape)

print("\nColumn names:")
print(df.columns.tolist())
print("\nFraudulent column values:")
print(df["fraudulent"].value_counts())