import pandas as pd
import joblib

MODEL_PATH = "ml/saved_brain.pkl"
DATA_PATH = "data/hard_validation_expenses.csv"


def main():
    model = joblib.load(MODEL_PATH)

    df = pd.read_csv(DATA_PATH)

    predictions = model.predict(df["Description"])

    df["Predicted"] = predictions

    errors = df[df["Category"] != df["Predicted"]]

    print("\n=== MISCLASSIFIED RECORDS ===\n")

    if errors.empty:
        print("No errors found.")
        return

    for _, row in errors.iterrows():
        print(
            f"Description: {row['Description']}\n"
            f"Actual: {row['Category']}\n"
            f"Predicted: {row['Predicted']}\n"
            f"{'-' * 50}"
        )

    errors.to_csv("data/model_errors.csv", index=False)

    print(f"\nSaved {len(errors)} errors to data/model_errors.csv")


if __name__ == "__main__":
    main()
