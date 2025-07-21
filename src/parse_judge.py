import pandas as pd
import json
from sklearn.metrics import precision_score, recall_score, f1_score

# Load Excel
df = pd.read_excel("/Users/marcocalamo/DALLE/judged_outputs_open.xlsx")

def evaluate_row(row):
    try:
        parsed = json.loads(row["judgment"])
        microservices = parsed.get("microservices", [])

        n_patterns = len(microservices)
        n_correct = sum(1 for ms in microservices if ms.get("is_correct", False))
        ratio = n_correct / n_patterns if n_patterns > 0 else None

        return pd.Series({
            "n_patterns": n_patterns,
            "n_correct": n_correct,
            "ratio": ratio
        })
    except Exception as e:
        raise e
        return pd.Series({
            "n_patterns": None,
            "n_correct": None,
            "ratio": None,
            "error": str(e)
        })

# Apply the logic row by row
metrics_df = df.apply(evaluate_row, axis=1)

# Combine with the original data
result_df = pd.concat([df, metrics_df], axis=1)

# Save to Excel
result_df.to_excel("pattern_accuracy_open.xlsx", index=False)
print("Saved to pattern_accuracy_open.xlsx")
